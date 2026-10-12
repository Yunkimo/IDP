// 日程页：列出全部日程/待办，支持添加/编辑/删除与勾选完成，数据同步到后端 SQLite。
const api = require('../../utils/api');
const { dateStr } = require('../../utils/datetime');

const EMPTY_FORM = { id: null, title: '', note: '', due_at: '' };

Page({
  data: {
    tasks: [],
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
      const today = dateStr(new Date());
      const tasks = (await api.getTasks()).map((t) => ({
        ...t,
        checked: !!t.done,
        dueText: t.due_at ? t.due_at.slice(0, 10) : '无截止日期',
        overdue: !!t.due_at && !t.done && t.due_at.slice(0, 10) < today,
      }));
      this.setData({ tasks });
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
    const t = e.currentTarget.dataset.task;
    this.setData({
      editing: true,
      form: {
        id: t.id,
        title: t.title,
        note: t.note || '',
        due_at: t.due_at ? t.due_at.slice(0, 10) : '',
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

  async submit() {
    const { form } = this.data;
    if (!form.title.trim()) {
      wx.showToast({ title: '请填写标题', icon: 'none' });
      return;
    }
    const payload = {
      title: form.title.trim(),
      note: form.note.trim(),
      due_at: form.due_at || null,
    };
    wx.showLoading({ title: '保存中' });
    try {
      if (form.id) {
        await api.updateTask(form.id, payload);
      } else {
        await api.createTask(payload);
      }
      this.setData({ editing: false });
      await this.load();
    } catch (err) {
      wx.showToast({ title: err.message, icon: 'none' });
    } finally {
      wx.hideLoading();
    }
  },

  async toggleDone(e) {
    const { id, done } = e.currentTarget.dataset;
    try {
      await api.updateTask(id, { done: done ? 0 : 1 });
      await this.load();
    } catch (err) {
      wx.showToast({ title: err.message, icon: 'none' });
    }
  },

  remove(e) {
    const { id, title } = e.currentTarget.dataset;
    wx.showModal({
      title: '删除日程',
      content: `确定删除「${title}」吗？后端数据库将同步删除。`,
      success: async (res) => {
        if (!res.confirm) {
          return;
        }
        wx.showLoading({ title: '删除中' });
        try {
          await api.deleteTask(id);
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
