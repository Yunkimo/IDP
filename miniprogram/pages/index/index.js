// 今日页：展示今天的课表与到期/逾期待办，支持勾选完成。
const api = require('../../utils/api');
const { WEEKDAY_LABELS, dateStr, todayDow } = require('../../utils/datetime');

Page({
  data: {
    todayLabel: '',
    courses: [],
    tasks: [],
    loading: false,
    error: '',
  },

  onShow() {
    this.loadToday();
  },

  onPullDownRefresh() {
    this.loadToday().finally(() => wx.stopPullDownRefresh());
  },

  async loadToday() {
    this.setData({ loading: true, error: '' });
    try {
      const [courses, tasks] = await Promise.all([api.getCourses(), api.getTasks()]);
      const dow = todayDow();
      const today = dateStr(new Date());
      this.setData({
        todayLabel: `${WEEKDAY_LABELS[dow - 1]} · ${today}`,
        courses: courses
          .filter((c) => c.day_of_week === dow)
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
