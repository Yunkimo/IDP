// 日期小工具：各页面共用的日期换算。

const WEEKDAY_LABELS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

/** Date → "YYYY-MM-DD"。 */
function dateStr(date) {
  const pad = (n) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

/** 今天对应的后端 day_of_week（1=周一 … 7=周日；JS getDay() 0=周日）。 */
function todayDow() {
  const day = new Date().getDay();
  return day === 0 ? 7 : day;
}

module.exports = { WEEKDAY_LABELS, dateStr, todayDow };
