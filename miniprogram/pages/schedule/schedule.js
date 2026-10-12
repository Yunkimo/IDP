// 课表页：按星期分组展示课程，支持添加/编辑/删除，数据同步到后端 SQLite。
const api = require('../../utils/api');
const { WEEKDAY_LABELS } = require('../../utils/datetime');

const EMPTY_FORM = {
  id: null,
  name: '',
  day_of_week: 1,
  start_time: '08:00',
  end_time: '09:40',
  location: '',
  weeksText: '',
};

// 后端 weeks 存 JSON 字符串（如 "[1,2,3]"），解析并压缩为 "1-3,5" 形式；空返回 ''。
function weeksToText(weeks) {
  let list = weeks;
  if (typeof weeks === 'string') {
    try {
      list = JSON.parse(weeks || '[]');
    } catch (err) {
      list = [];
    }
  }
  list = Array.isArray(list) ? list : [];
  const ranges = [];
  for (const w of list) {
    const last = ranges[ranges.length - 1];
    if (last && w === last.end + 1) {
      last.end = w;
    } else {
      ranges.push({ start: w, end: w });
    }
  }
  return ranges.map((r) => (r.start === r.end ? `${r.start}` : `${r.start}-${r.end}`)).join(',');
}

// 表单周次输入（"1-16" / "1,3,5" / 空=全周）解析为数字数组；格式错误返回 null。
function parseWeeks(text) {
  const raw = String(text || '').trim();
  if (!raw) {
    return [];
  }
  const weeks = [];
  for (const part of raw.split(/[,，、\s]+/)) {
    if (!part) {
      continue;
    }
    const match = part.match(/^(\d+)-(\d+)$/);
    if (match) {
      const start = Number(match[1]);
      const end = Number(match[2]);
      if (start > end) {
        return null;
      }
      for (let w = start; w <= end; w += 1) {
        weeks.push(w);
      }
    } else if (/^\d+$/.test(part)) {
      weeks.push(Number(part));
    } else {
      return null;
    }
  }
  return weeks;
}

Page({
  data: {
    weekOptions: WEEKDAY_LABELS,
    weekDays: [],
    loading: false,
    error: '',
    editing: false,
    form: { ...EMPTY_FORM },
  },

  onShow() {
    this.load();
  },

  onPullDownRefresh() {
    this.load().finally(() => wx.stopPullDownRefresh());
  },

  async load() {
    this.setData({ loading: true, error: '' });
    try {
      const courses = await api.getCourses();
      const weekDays = WEEKDAY_LABELS.map((label, i) => ({
        day: i + 1,
        label,
        courses: courses
          .filter((c) => c.day_of_week === i + 1)
          .sort((a, b) => a.start_time.localeCompare(b.start_time))
          .map((c) => ({ ...c, weeksText: weeksToText(c.weeks) || '全周' })),
      }));
      this.setData({ weekDays });
    } catch (err) {
      this.setData({ error: err.message || '加载失败' });
    } finally {
      this.setData({ loading: false });
    }
  },

  openAdd() {
    this.setData({ editing: true, form: { ...EMPTY_FORM } });
  },

  openEdit(e) {
    const c = e.currentTarget.dataset.course;
    this.setData({
      editing: true,
      form: {
        id: c.id,
        name: c.name,
        day_of_week: c.day_of_week,
        start_time: c.start_time,
        end_time: c.end_time,
        location: c.location || '',
        weeksText: weeksToText(c.weeks),
      },
    });
  },

  closeForm() {
    this.setData({ editing: false });
  },

  onFormInput(e) {
    const field = e.currentTarget.dataset.field;
    this.setData({ [`form.${field}`]: e.detail.value });
  },

  onWeekPicker(e) {
    this.setData({ 'form.day_of_week': Number(e.detail.value) + 1 });
  },

  async submit() {
    const { form } = this.data;
    if (!form.name.trim()) {
      wx.showToast({ title: '请填写课程名称', icon: 'none' });
      return;
    }
    if (form.start_time >= form.end_time) {
      wx.showToast({ title: '结束时间需晚于开始时间', icon: 'none' });
      return;
    }
    const weeks = parseWeeks(form.weeksText);
    if (weeks === null) {
      wx.showToast({ title: '周次格式不正确（如 1-16 或 1,3,5）', icon: 'none' });
      return;
    }
    const payload = {
      name: form.name.trim(),
      day_of_week: form.day_of_week,
      start_time: form.start_time,
      end_time: form.end_time,
      location: form.location.trim(),
      weeks,
    };
    wx.showLoading({ title: '保存中' });
    try {
      if (form.id) {
        await api.updateCourse(form.id, payload);
      } else {
        await api.createCourse(payload);
      }
      this.setData({ editing: false });
      await this.load();
    } catch (err) {
      wx.showToast({ title: err.message, icon: 'none' });
    } finally {
      wx.hideLoading();
    }
  },

  remove(e) {
    const { id, name } = e.currentTarget.dataset;
    wx.showModal({
      title: '删除课程',
      content: `确定删除「${name}」吗？后端数据库将同步删除。`,
      success: async (res) => {
        if (!res.confirm) {
          return;
        }
        wx.showLoading({ title: '删除中' });
        try {
          await api.deleteCourse(id);
          await this.load();
        } catch (err) {
          wx.showToast({ title: err.message, icon: 'none' });
        } finally {
          wx.hideLoading();
        }
      },
    });
  },

  retry() {
    this.load();
  },
});
