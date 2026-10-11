/* 通用 Live2D 渲染（Cubism 4）：模型入口从 URL 参数读取，动作组/表情从模型元数据动态发现。
   交互：短待机随机待机动作 → 长时间待机荡秋千；点击模型脸切换表情（自定义识别区 CLICK_ZONES）。 */
window.__jsErrors = [];
window.addEventListener('error', function (e) {
  window.__jsErrors.push('error: ' + (e.message || e.type));
});
window.addEventListener('unhandledrejection', function (e) {
  var r = e.reason;
  window.__jsErrors.push('rejection: ' + ((r && r.message) || r));
});

// 超过该时长（毫秒）无交互，待机时改玩荡秋千
var LONG_IDLE_MS = 12000;

// 自定义点脸识别区：模型局部归一化坐标（0~1，相对模型宽高；0,0 左上角，0.5,0.5 中心）。
// 完全不用模型自带的 HitAreas（其 ArtMesh 包围盒含大量透明区、判定过大），
// 这里手动圈定小矩形，精确控制判定位置与大小；想改就改下表。
var CLICK_ZONES = [
  // 示例（按你的模型调整）：{ expr: "表情名", x: 0.5, y: 0.5, w: 0.08, h: 0.10 },
];

(async function () {
  try {
    window.PIXI = PIXI; // 插件通过 window.PIXI.Ticker 自动驱动更新

    if (!PIXI || !PIXI.live2d) {
      throw new Error('PIXI.live2d 未加载 (typeof PIXI=' + typeof PIXI + ')');
    }

    var Live2DModel = PIXI.live2d.Live2DModel;
    Live2DModel.registerTicker(PIXI.Ticker);

    var app = new PIXI.Application({
      backgroundAlpha: 0, // 透明画布
      resizeTo: window,
      antialias: true,
      autoDensity: true,
      resolution: Math.max(1, window.devicePixelRatio || 1),
    });
    document.body.appendChild(app.view);

    // 模型入口（相对路径，如 mymodel/MyModel.model3.json），由 URL 参数 entry 指定
    var entry = (new URLSearchParams(location.search)).get('entry') || '';

    // 从模型元数据发现动作组、表情名（避免硬编码某个模型）
    var motions = {};
    var expressionNames = [];
    try {
      var meta = await (await fetch(entry)).json();
      var refs = meta.FileReferences || {};
      motions = refs.Motions || {};
      (refs.Expressions || []).forEach(function (e) {
        if (e && e.Name) expressionNames.push(e.Name);
      });
    } catch (e) {
      window.__jsErrors.push('meta: ' + ((e && e.message) || e));
    }

    var motionGroups = Object.keys(motions);
    var groupSizes = {};
    motionGroups.forEach(function (g) { groupSizes[g] = (motions[g] || []).length; });

    var model = await Live2DModel.from(entry);
    app.stage.addChild(model);
    model.autoInteract = true; // 眨眼 / 视线跟随 / 物理

    function layout() {
      var w = model.width || 1;
      var h = model.height || 1;
      var scale = Math.min(app.screen.width / w, app.screen.height / h) * 0.96;
      model.scale.set(scale);
      model.anchor.set(0.5, 0.5);
      model.x = app.screen.width / 2;
      model.y = app.screen.height * 0.52;
    }
    layout();
    window.addEventListener('resize', layout);

    // 动作组分类：区分「带动作文件(.motion3.json)的真实动作」与「纯表情/开关」组，
    // 避免随机动作播放到「表情#2 / 表情2#3 / 表情3#4」这类只会设置表情的组。
    function inGroup(name) { return function (g) { return (new RegExp(name, 'i')).test(g); }; }
    function groupHasFile(g) { return (motions[g] || []).some(function (m) { return !!m.File; }); }

    var fileGroups = motionGroups.filter(groupHasFile);  // 有真实动作文件的组
    var start = motionGroups.filter(inGroup('^start$|开场|开始|初始化'));
    var idleNamed = motionGroups.filter(inGroup('idle|tick|待机'));
    var idle = idleNamed.length
      ? idleNamed
      : fileGroups.filter(function (g) { return start.indexOf(g) < 0; });
    var action = fileGroups.filter(function (g) {
      return idle.indexOf(g) < 0 && start.indexOf(g) < 0;
    });
    if (!action.length) action = fileGroups.slice();

    // 荡秋千动作（长时间待机专用）：按动作名定位，兼容不同模型
    var swingMotion = null;
    motionGroups.forEach(function (g) {
      (motions[g] || []).forEach(function (m, i) {
        if (m && m.File && /秋千|swing/i.test(m.Name || '')) swingMotion = { group: g, index: i };
      });
    });

    // 随机播一组动作；skipFirst 跳过下标 0（Live2D 惯例：第 0 个常是「回正」复位），
    // exclude 用于把荡秋千从短待机里剔除，让它成为「长时间待机」专属动作。
    function pickMotion(groups, skipFirst, exclude) {
      if (!groups.length) return Promise.resolve();
      var g = groups[Math.floor(Math.random() * groups.length)];
      var size = groupSizes[g] || 0;
      if (!size) return Promise.resolve();
      var candidates = [];
      for (var i = 0; i < size; i++) {
        if (skipFirst && i === 0) continue;
        if (exclude && exclude.group === g && exclude.index === i) continue;
        candidates.push(i);
      }
      if (!candidates.length) return Promise.resolve();
      var idx = candidates[Math.floor(Math.random() * candidates.length)];
      return model.motion(g, idx);
    }

    // 待机循环：短待机随机待机动作；长时间无交互则荡秋千
    var lastInteraction = Date.now();
    var idleTimer = null;
    function scheduleIdle(delay) { clearTimeout(idleTimer); idleTimer = setTimeout(playIdle, delay); }
    async function playIdle() {
      try {
        if (swingMotion && Date.now() - lastInteraction > LONG_IDLE_MS) {
          await model.motion(swingMotion.group, swingMotion.index);
          scheduleIdle(400); // 荡完接着荡，直到有交互打断
        } else {
          await pickMotion(idle, false, swingMotion);
          scheduleIdle(2200);
        }
      } catch (e) {
        scheduleIdle(3000);
      }
    }
    function onInteraction() {
      lastInteraction = Date.now();
      // 停止当前动作（尤其循环的荡秋千）：它不播完就永远占着动作优先级，
      // 若不显式 stop，交互后新动作会被 reject，宠物会一直荡下去。
      try {
        var mm = model.internalModel && model.internalModel.motionManager;
        if (mm && mm.stopAllMotions) mm.stopAllMotions();
      } catch (e) {}
      scheduleIdle(1200);
    }
    scheduleIdle(1200);

    // 点脸换表情：点击坐标 → 模型局部归一化坐标 → 匹配自定义识别区 CLICK_ZONES
    function tapAt(x, y) {
      try {
        var p = new PIXI.Point(x, y);
        model.toModelPosition(p, p); // 画布坐标 → 模型局部坐标
        var im = model.internalModel;
        var nx = p.x / im.originalWidth;
        var ny = p.y / im.originalHeight;
        for (var i = 0; i < CLICK_ZONES.length; i++) {
          var z = CLICK_ZONES[i];
          if (Math.abs(nx - z.x) <= z.w / 2 && Math.abs(ny - z.y) <= z.h / 2) {
            model.expression(z.expr);
            onInteraction();
            return true;
          }
        }
        // 点空白（收起/展开输入框）也是交互：同样要停止荡秋千并重新计时
        onInteraction();
      } catch (e) {
        window.__jsErrors.push('tap: ' + ((e && e.message) || e));
      }
      return false;
    }
    // 随机换一个表情（语音输入时的反应），排除「回正」复位项
    function randomExpression() {
      var names = expressionNames.filter(function (n) { return !/回正|reset/i.test(n); });
      if (!names.length) names = expressionNames;
      if (!names.length) return;
      model.expression(names[Math.floor(Math.random() * names.length)]);
      onInteraction();
    }

    window.__live2dReady = true;
    window.__live2dSize = { width: model.width, height: model.height };
    window.live2d = {
      model: model,
      layout: layout,
      motion: function (g) {
        onInteraction();
        if (g && groupSizes[g]) {
          return pickMotion([g], true);
        }
        return pickMotion(action, true);
      },
      expression: function (n) { model.expression(n); },
      resetExpression: function () {
        // 复位表情到默认（清除疑惑等），供成功回复后恢复正常神态
        try {
          var em = model.internalModel && model.internalModel.motionManager
            && model.internalModel.motionManager.expressionManager;
          if (em && em.resetExpression) em.resetExpression();
        } catch (e) {}
      },
      tapAt: tapAt,
      randomExpression: randomExpression,
    };
    window.__snapshot = function () {
      try {
        return app.renderer.extract.canvas(app.stage).toDataURL('image/png');
      } catch (e) {
        return 'ERROR:' + e;
      }
    };
  } catch (e) {
    window.__live2dReady = false;
    window.__live2dError = String((e && e.message) || e);
    window.__jsErrors.push('init: ' + window.__live2dError);
  }
})();
