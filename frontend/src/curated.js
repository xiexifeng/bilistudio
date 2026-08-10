/**
 * 精选教育/手工UP主 — 适合小学-初中孩子
 * mid: B站用户ID
 * category: 分类标签
 * tags: 适合的年龄段/学科
 */
export const curatedUpers = [
  {
    mid: 14804670,
    name: '无穷小亮的科普日常',
    category: '自然科普',
    tags: ['生物', '自然', '动物'],
    desc: '《博物》杂志副主编，鉴定网络热门生物',
    icon: '🦎',
  },
  {
    mid: 9458053,
    name: '李永乐老师官方',
    category: '数学物理',
    tags: ['数学', '物理', '思维'],
    desc: '用有趣的方式讲数学和物理知识',
    icon: '📐',
  },
  {
    mid: 280793434,
    name: '手工耿',
    category: '创意手工',
    tags: ['手工', '发明', '创意'],
    desc: '无用良品发明家，激发创造力和动手兴趣',
    icon: '🔧',
  },
  {
    mid: 254463269,
    name: '毕导',
    category: '趣味科学',
    tags: ['科学', '实验', '趣味'],
    desc: '用搞笑的方式做正经科学实验',
    icon: '🧪',
  },
  // ===== 小学数学 =====
  {
    mid: 431569803,
    name: '数学林老师',
    category: '小学数学',
    tags: ['数学', '小学', '讲题'],
    desc: '专注中小学数学教学，思路清晰，讲解透彻',
    icon: '✏️',
  },
  {
    mid: 503133989,
    name: '学而思网校教师集结号',
    category: '小学数学',
    tags: ['数学', '小学', '全科'],
    desc: '学而思网校名师，覆盖小学到初中数学思维',
    icon: '🏫',
  },
  {
    mid: 14229967,
    name: '一数',
    category: '数学教学',
    tags: ['数学', '小学', '初中', '解题'],
    desc: '小学数学到初中数学知识点讲解，通俗易懂',
    icon: '🧮',
  },
  {
    mid: 395877542,
    name: '不刷题的吴姥姥',
    category: '物理实验',
    tags: ['物理', '实验', '趣味'],
    desc: '同济大学退休教授，用生活物品做物理实验',
    icon: '⚡',
  },
  {
    mid: 5581898,
    name: '飞碟说',
    category: '知识科普',
    tags: ['百科', '冷知识', '动画'],
    desc: '动画科普百科知识，有趣有料',
    icon: '🛸',
  },
  // ===== 小学英语 =====
  {
    mid: 483162496,
    name: '英语兔',
    category: '小学英语',
    tags: ['英语', '发音', '语法', '小学'],
    desc: '1300万粉大V，地道英语发音教学，轻松入门',
    icon: '🐰',
  },
  {
    mid: 388576777,
    name: '英语的平行世界',
    category: '小学英语',
    tags: ['英语', '启蒙', '语法', '单词'],
    desc: '590万粉，系统英语教学，从零基础到进阶',
    icon: '🌍',
  },
  // ===== 小学语文 =====
  {
    mid: 265589608,
    name: '-古人云-',
    category: '小学语文',
    tags: ['语文', '古诗', '国学', '历史'],
    desc: '趣味讲解古诗词和传统文化',
    icon: '📜',
  },
  {
    mid: 354875574,
    name: '牛哥小学作文秀',
    category: '小学语文',
    tags: ['语文', '作文', '写作', '小学'],
    desc: '26万粉，每天优秀作文展示，搞定小学作文',
    icon: '✍️',
  },
]

// 首页分类快捷搜索
export const searchCategories = [
  { label: '✏️ 小学数学', query: '小学数学 讲解 启蒙' },
  { label: '🐰 英语启蒙', query: '小学英语 自然拼读 启蒙' },
  { label: '📜 古诗与作文', query: '小学语文 古诗 作文' },
  { label: '🧪 科学实验', query: '科学实验 趣味' },
  { label: '📐 初中数学', query: '初中数学 讲解 知识点' },
  { label: '🔧 手工制作', query: '手工制作 DIY' },
  { label: '🦎 自然科普', query: '科普 自然 生物' },
  { label: '⚡ 物理实验', query: '物理实验 演示' },
  { label: '💻 编程入门', query: '少儿编程 Scratch' },
  { label: '🎨 绘画手工', query: '绘画教程 手工' },
]

/**
 * 学习路线/课程定义
 * 每条路线包含多个阶段，家长可以为每个阶段收藏视频并打卡
 */
export const learningPaths = [
  {
    id: 'math',
    title: '🧮 数学启蒙',
    desc: '从认数到四则运算，系统建立数学思维',
    color: '#FF6B35',
    bg: '#FFF3E0',
    stages: [
      { id: 'math-1', title: '认识数字', desc: '1-100 数数、读写、大小比较', search: '认识数字 数学启蒙' },
      { id: 'math-2', title: '10以内加减', desc: '凑十法、破十法、口算练习', search: '10以内加减法 凑十法' },
      { id: 'math-3', title: '20以内进退位', desc: '进位加法、退位减法', search: '20以内加减法 进退位' },
      { id: 'math-4', title: '乘法口诀', desc: '理解乘法、背诵口诀、简单应用', search: '乘法口诀 小学数学' },
      { id: 'math-5', title: '除法初步', desc: '平均分、表内除法、有余数除法', search: '除法 小学数学 讲解' },
    ],
  },
  {
    id: 'english',
    title: '🐰 英语启蒙',
    desc: '从字母到简单对话，快乐学英语',
    color: '#45B7D1',
    bg: '#E0F7FA',
    stages: [
      { id: 'eng-1', title: '字母与发音', desc: '26个字母认读、自然拼读入门', search: '英语字母 自然拼读 启蒙' },
      { id: 'eng-2', title: '基础词汇', desc: '颜色、数字、动物、家庭成员', search: '英语基础词汇 小学 启蒙' },
      { id: 'eng-3', title: '简单句型', desc: 'What/How/Can 开头的简单问答', search: '小学英语 简单句型 对话' },
      { id: 'eng-4', title: '绘本阅读', desc: '英文绘本跟读、故事理解', search: '英文绘本 阅读 小学' },
    ],
  },
  {
    id: 'science',
    title: '🧪 科学探索',
    desc: '动手实验、观察自然、培养科学素养',
    color: '#10B981',
    bg: '#D1FAE5',
    stages: [
      { id: 'sci-1', title: '趣味物理实验', desc: '用日常物品做简单物理实验', search: '物理实验 趣味 简单' },
      { id: 'sci-2', title: '化学小魔术', desc: '安全的家庭化学小实验', search: '化学实验 简单 安全' },
      { id: 'sci-3', title: '生物与自然', desc: '认识动植物、了解生态系统', search: '科普 动物 植物 自然' },
      { id: 'sci-4', title: '天文地理', desc: '太阳系、地球、天气现象', search: '天文 地理 科普 儿童' },
    ],
  },
  {
    id: 'code',
    title: '💻 编程入门',
    desc: '图形化编程起步，培养计算思维',
    color: '#8B5CF6',
    bg: '#EDE9FE',
    stages: [
      { id: 'code-1', title: 'Scratch初体验', desc: '认识界面、角色移动、简单动画', search: 'Scratch 入门 教程' },
      { id: 'code-2', title: '事件与循环', desc: '点击事件、重复执行、条件判断', search: 'Scratch 条件 循环 讲解' },
      { id: 'code-3', title: '做一个游戏', desc: '综合运用，完成一个完整小游戏', search: 'Scratch 游戏 制作 教程' },
    ],
  },
  {
    id: 'chinese',
    title: '📜 语文素养',
    desc: '古诗积累、作文入门、文化启蒙',
    color: '#EC4899',
    bg: '#FCE7F3',
    stages: [
      { id: 'cn-1', title: '古诗启蒙', desc: '唐诗宋词选读、诗词意境理解', search: '小学古诗 讲解 动画' },
      { id: 'cn-2', title: '成语故事', desc: '常用成语的来源和用法', search: '成语故事 动画 儿童' },
      { id: 'cn-3', title: '作文入门', desc: '看图写话、段落写作、日记', search: '小学作文 写作 方法' },
      { id: 'cn-4', title: '阅读积累', desc: '名著导读、阅读方法、好词好句', search: '儿童阅读 名著 导读' },
    ],
  },
]
