// 复制本文件为 miniprogram/config.js 并填入真实值。
// config.js 已加入 .gitignore —— API Key 属于密钥，不提交进仓库（见 docs/security.md）。
module.exports = {
  // 后端地址：开发期可用局域网 IP 或内网穿透地址（见 docs/deploy.md，任务 C4）
  baseUrl: 'http://127.0.0.1:8001',
  // 与 backend/.env 的 API_TOKEN 保持一致；请求时经 X-API-Key 请求头发送，由后端校验
  apiKey: '填入 backend/.env 的 API_TOKEN',
};
