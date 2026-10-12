// 今日页：展示今天的课表与到期/逾期待办，支持勾选完成。
// 课表按「本周周次」过滤：weeks 不含当前周的课程不显示（无周次 = 全周）。
const api = require('../../utils/api');
const {
  WEEKDAY_LABELS,
  WEEK_OPTIONS,
  dateStr,
  todayDow,
  getCurrentWeek,
  setCurrentWeek,
  isActiveWeek,
} = require('../../utils/datetime');

Page({
  data: {
    currentWeek: 6,
    weekOptions: WEEK_OPTIONS,
    todayLabel: '',
    courses: [],
    tasks: [],
    loading: false,
    error: '',
  },

  onShow() {
    this.setData({ currentWeek: getCurrentWeek() });
    this.loadToday();
  },

  onPullDownRefresh() {
    this.loadToday().finally(() => wx.stopPullDownRefresh());
  },

  // 切换本周周次：保存后按新周次重新过滤
  onWeekPick(e) {
    const week = Number(e.detail.value) + 1;
    setCurrentWeek(week);
    this.setData({ currentWeek: week });
    this.loadToday();
  },

  async loadToday() {
    this.setData({ loading: true, error: '' });
    try {
      const [courses, tasks] = await Promise.all([api.getCourses(), api.getTasks()]);
      const dow = todayDow();
      const today = dateStr(new Date());
      this.setData({
        todayLabel: `第${this.data.currentWeek}周 · ${WEEKDAY_LABELS[dow - 1]} · ${today}`,
        courses: courses
          .filter((c) => c.day_of_week === dow && isActiveWeek(c, this.data.currentWeek))
          .sort((a, b) => a.start_time.localeCompare(b.start_time)),
        tasks: tasks
          .filter((t) => !t.done && t.due_at && t.due_at.slice(0, 10) <= today)
          .map((t) => ({
            ...t,
            checked: false,
            dueText: t.due_at.slice(0, 10),
            overdue: t.due_at.slice(0, 10) < today,
          })),
      });
    } catch (err) {
      this.setData({ error: err.message || '加载失败' });
    } finally {
      this.setData({ loading: false });
    }
  },

  async toggleTask(e) {
    const { id, done } = e.currentTarget.dataset;
    try {
      await api.updateTask(id, { done: done ? 0 : 1 });
      await this.loadToday();
    } catch (err) {
      wx.showToast({ title: err.message, icon: 'none' });
    }
  },

  retry() {
    this.loadToday();
  },
});
