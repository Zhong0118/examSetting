const levels = ['小学', '初中', '高中', '大学'];
const grades1 = [
    '一年级',
    '二年级',
    '三年级',
    '四年级',
    '五年级',
    '六年级'
];
const grades2 = ['一年级', '二年级', '三年级',];
const primarySubjects = ['语文', '数学', '英语', '思政'];
const Subjects = [
    '语文',
    '数学',
    '英语',
    '物理',
    '化学',
    '生物',
    '政治',
    '历史',
    '地理'
];
const advancedSubjects = [
    '高数',
    '线性代数',
    '马克思主义',
    '大学物理'
];
const topics = [
    '单选',
    '多选',
    '填空',
    '判断',
    '解答',
];
const primaryChinese = [
    '诗词默写',
    '作文日记',
    '拼音写字',
    '小阅读',
];
const primaryEnglish = [
    '单词默写',
    '中译英',
    '英译中',
    '写作',
];
const primaryMath = [
    '基础运算',
    '混合运算',
    '图形',
    '角度',
];
const Chinese = [
    '阅读理解',
    '作文',
    '诗词阅读',
];
const English = [
    '七选五',
    '阅读理解',
    '中译英',
    '写作',
    '纠错',
];
const Maths = [
    '方程式',
    '三角函数',
    '统计',
    '概率',
    '导数',
    '图形坐标'
];
const Physical = [
    '压力',
    '浮力',
    '摩擦力',
    '光学',
    '电学',
    '磁学',
]
const Chemistry = [
    '有机化学', '无机化学', '化学方程式', '化学分析'
]
const Biology = ['细胞生物学', '遗传学', '生态学'];
const Politics = ['政治理论', '时事政治', '法律基础'];
const Histories = ['古代史', '近代史', '世界史'];
const Geography = ['自然地理', '人文地理', '地图学'];
const advancedPhysics = ['压力',
    '浮力',
    '摩擦力',
    '光学',
    '电学',
    '磁学',
    '量子力学',
    '相对论'
];
const advancedMath = ['微积分', '求导', '求极限', '二重积分', '无穷级数', '曲线曲面积分'];
const linearAlgebra = ['向量', '矩阵', '线性方程组'];
const marxism = ['哲学', '政治经济学', '社会学'];


const options = [
    {
        value: levels[0],
        label: levels[0],
        children: [
            {
                // 一年级
                value: grades1[0],
                label: grades1[0],
                children: [
                    {
                        // 语文
                        value: primarySubjects[0],
                        label: primarySubjects[0],
                        children: [
                            {
                                value: primaryChinese[2],
                                label: primaryChinese[2],
                            },
                            {
                                value: primaryChinese[3],
                                label: primaryChinese[3],
                            },
                            {
                                value: primaryChinese[1],
                                label: primaryChinese[1],
                            },
                        ],
                    },
                    {
                        // 数学
                        value: primarySubjects[1],
                        label: primarySubjects[1],
                        children: [
                            {
                                value: primaryMath[0],
                                label: primaryMath[0],
                            },
                            {
                                value: primaryMath[1],
                                label: primaryMath[1],
                            },
                        ],
                    },
                ],
            },
            {
                // 二年级
                value: grades1[1],
                label: grades1[1],
                children: [
                    {
                        // 语文
                        value: primarySubjects[0],
                        label: primarySubjects[0],
                        children: [
                            {
                                value: primaryChinese[2],
                                label: primaryChinese[2],
                            },
                            {
                                value: primaryChinese[3],
                                label: primaryChinese[3],
                            },
                            {
                                value: primaryChinese[1],
                                label: primaryChinese[1],
                            },
                        ],
                    },
                    {
                        // 数学
                        value: primarySubjects[1],
                        label: primarySubjects[1],
                        children: [
                            {
                                value: primaryMath[0],
                                label: primaryMath[0],
                            },
                            {
                                value: primaryMath[1],
                                label: primaryMath[1],
                            },
                            {
                                value: primaryMath[2],
                                label: primaryMath[2],
                            },
                        ],
                    },
                ],
            },
            {
                // 三年级
                value: grades1[2],
                label: grades1[2],
                children: [
                    {
                        // 语文
                        value: primarySubjects[0],
                        label: primarySubjects[0],
                        children: [
                            {
                                value: primaryChinese[2],
                                label: primaryChinese[2],
                            },
                            {
                                value: primaryChinese[3],
                                label: primaryChinese[3],
                            },
                            {
                                value: primaryChinese[0],
                                label: primaryChinese[0],
                            },
                            {
                                value: primaryChinese[1],
                                label: primaryChinese[1],
                            },
                        ],
                    },
                    {
                        // 数学
                        value: primarySubjects[1],
                        label: primarySubjects[1],
                        children: [
                            {
                                value: primaryMath[0],
                                label: primaryMath[0],
                            },
                            {
                                value: primaryMath[1],
                                label: primaryMath[1],
                            },
                            {
                                value: primaryMath[2],
                                label: primaryMath[2],
                            },
                            {
                                value: primaryMath[3],
                                label: primaryMath[3],
                            },
                        ],
                    },
                    {
                        // 英语
                        value: primarySubjects[2],
                        label: primarySubjects[2],
                        children: [
                            {
                                value: primaryEnglish[0],
                                label: primaryEnglish[0],
                            },
                            {
                                value: primaryEnglish[3],
                                label: primaryEnglish[3],
                            },
                        ],
                    },
                    {
                        // 思政
                        value: primarySubjects[3],
                        label: primarySubjects[3],
                    },
                ],
            },
            {
                // 四年级
                value: grades1[3],
                label: grades1[3],
                children: [
                    {
                        // 语文
                        value: primarySubjects[0],
                        label: primarySubjects[0],
                        children: [
                            {
                                value: primaryChinese[2],
                                label: primaryChinese[2],
                            },
                            {
                                value: primaryChinese[3],
                                label: primaryChinese[3],
                            },
                            {
                                value: primaryChinese[0],
                                label: primaryChinese[0],
                            },
                            {
                                value: primaryChinese[1],
                                label: primaryChinese[1],
                            },
                        ],
                    },
                    {
                        // 数学
                        value: primarySubjects[1],
                        label: primarySubjects[1],
                        children: [
                            {
                                value: primaryMath[0],
                                label: primaryMath[0],
                            },
                            {
                                value: primaryMath[1],
                                label: primaryMath[1],
                            },
                            {
                                value: primaryMath[2],
                                label: primaryMath[2],
                            },
                            {
                                value: primaryMath[3],
                                label: primaryMath[3],
                            },
                        ],
                    },
                    {
                        // 英语
                        value: primarySubjects[2],
                        label: primarySubjects[2],
                        children: [
                            {
                                value: primaryEnglish[0],
                                label: primaryEnglish[0],
                            },
                            {
                                value: primaryEnglish[3],
                                label: primaryEnglish[3],
                            },
                        ],
                    },
                    {
                        // 思政
                        value: primarySubjects[3],
                        label: primarySubjects[3],
                    },
                ],
            },
            {
                // 五年级
                value: grades1[4],
                label: grades1[4],
                children: [
                    {
                        // 语文
                        value: primarySubjects[0],
                        label: primarySubjects[0],
                        children: [
                            {
                                value: primaryChinese[2],
                                label: primaryChinese[2],
                            },
                            {
                                value: primaryChinese[3],
                                label: primaryChinese[3],
                            },
                            {
                                value: primaryChinese[0],
                                label: primaryChinese[0],
                            },
                            {
                                value: primaryChinese[1],
                                label: primaryChinese[1],
                            },
                        ],
                    },
                    {
                        // 数学
                        value: primarySubjects[1],
                        label: primarySubjects[1],
                        children: [
                            {
                                value: primaryMath[0],
                                label: primaryMath[0],
                            },
                            {
                                value: primaryMath[1],
                                label: primaryMath[1],
                            },
                            {
                                value: primaryMath[2],
                                label: primaryMath[2],
                            },
                            {
                                value: primaryMath[3],
                                label: primaryMath[3],
                            },
                        ],
                    },
                    {
                        // 英语
                        value: primarySubjects[2],
                        label: primarySubjects[2],
                        children: [
                            {
                                value: primaryEnglish[0],
                                label: primaryEnglish[0],
                            },
                            {
                                value: primaryEnglish[2],
                                label: primaryEnglish[2],
                            },
                            {
                                value: primaryEnglish[3],
                                label: primaryEnglish[3],
                            },
                        ],
                    },
                    {
                        // 思政
                        value: primarySubjects[3],
                        label: primarySubjects[3],
                    },
                ],
            },
            {
                // 六年级
                value: grades1[5],
                label: grades1[5],
                children: [
                    {
                        // 语文
                        value: primarySubjects[0],
                        label: primarySubjects[0],
                        children: [
                            {
                                value: primaryChinese[2],
                                label: primaryChinese[2],
                            },
                            {
                                value: primaryChinese[3],
                                label: primaryChinese[3],
                            },
                            {
                                value: primaryChinese[0],
                                label: primaryChinese[0],
                            },
                            {
                                value: primaryChinese[1],
                                label: primaryChinese[1],
                            },
                        ],
                    },
                    {
                        // 数学
                        value: primarySubjects[1],
                        label: primarySubjects[1],
                        children: [
                            {
                                value: primaryMath[0],
                                label: primaryMath[0],
                            },
                            {
                                value: primaryMath[1],
                                label: primaryMath[1],
                            },
                            {
                                value: primaryMath[2],
                                label: primaryMath[2],
                            },
                            {
                                value: primaryMath[3],
                                label: primaryMath[3],
                            },
                        ],
                    },
                    {
                        // 英语
                        value: primarySubjects[2],
                        label: primarySubjects[2],
                        children: [
                            {
                                value: primaryEnglish[0],
                                label: primaryEnglish[0],
                            },
                            {
                                value: primaryEnglish[1],
                                label: primaryEnglish[1],
                            },
                            {
                                value: primaryEnglish[2],
                                label: primaryEnglish[2],
                            },
                            {
                                value: primaryEnglish[3],
                                label: primaryEnglish[3],
                            },
                        ],
                    },
                    {
                        // 思政
                        value: primarySubjects[3],
                        label: primarySubjects[3],
                    },
                ],
            },
        ],
    },
    //   初中
    {
        value: levels[1],
        label: levels[1],
        children: [
            {
                // 初一
                value: grades1[0],
                label: grades1[0],
                children: [
                    {
                        // 语文
                        value: Subjects[0],
                        label: Subjects[0],
                        children: [
                            {
                                value: Chinese[0],
                                label: Chinese[0],
                            },
                            {
                                value: Chinese[1],
                                label: Chinese[1],
                            },
                        ],
                    },
                    {
                        // 数学
                        value: Subjects[1],
                        label: Subjects[1],
                        children: [
                            {
                                value: Maths[0],
                                label: Maths[0],
                            },
                            {
                                value: Maths[1],
                                label: Maths[1],
                            },
                            {
                                value: Maths[5],
                                label: Maths[5],
                            },
                        ],
                    },
                    {
                        // 英语
                        value: Subjects[2],
                        label: Subjects[2],
                        children: [
                            {
                                value: English[0],
                                label: English[0],
                            },
                            {
                                value: English[1],
                                label: English[1],
                            },
                            {
                                value: English[2],
                                label: English[2],
                            },
                            {
                                value: English[3],
                                label: English[3],
                            },
                            {
                                value: English[4],
                                label: English[4],
                            },
                        ],
                    },
                    {
                        // 生物
                        value: Subjects[5],
                        label: Subjects[5],
                        children: [
                            {
                                value: Biology[0],
                                label: Biology[0],
                            },
                            {
                                value: Biology[2],
                                label: Biology[2],
                            },
                        ],
                    },
                    {
                        // 地理
                        value: Subjects[8],
                        label: Subjects[8],
                        children: [
                            {
                                value: Geography[0],
                                label: Geography[0],
                            },
                            {
                                value: Geography[1],
                                label: Geography[1],
                            },
                        ],
                    },
                    {
                        // 政治
                        value: Subjects[6],
                        label: Subjects[6],
                        children: [
                            {
                                value: Politics[0],
                                label: Politics[0],
                            },
                        ],
                    },
                    {
                        // 历史
                        value: Subjects[7],
                        label: Subjects[7],
                        children: [
                            {
                                value: Histories[0],
                                label: Histories[0],
                            },
                        ],
                    },
                ],
            },
            {
                // 初二
                value: grades1[1],
                label: grades1[1],
                children: [
                    {
                        // 语文
                        value: Subjects[0],
                        label: Subjects[0],
                        children: [
                            {
                                value: Chinese[0],
                                label: Chinese[0],
                            },
                            {
                                value: Chinese[1],
                                label: Chinese[1],
                            },
                        ],
                    },
                    {
                        // 数学
                        value: Subjects[1],
                        label: Subjects[1],
                        children: [
                            {
                                value: Maths[0],
                                label: Maths[0],
                            },
                            {
                                value: Maths[1],
                                label: Maths[1],
                            },
                            {
                                value: Maths[2],
                                label: Maths[2],
                            },
                            {
                                value: Maths[5],
                                label: Maths[5],
                            },
                        ],
                    },
                    {
                        // 英语
                        value: Subjects[2],
                        label: Subjects[2],
                        children: [
                            {
                                value: English[0],
                                label: English[0],
                            },
                            {
                                value: English[1],
                                label: English[1],
                            },
                            {
                                value: English[2],
                                label: English[2],
                            },
                            {
                                value: English[3],
                                label: English[3],
                            },
                            {
                                value: English[4],
                                label: English[4],
                            },
                        ],
                    },
                    {
                        // 物理
                        value: Subjects[3],
                        label: Subjects[3],
                        children: [
                            {
                                value: Physical[0],
                                label: Physical[0],
                            },
                            {
                                value: Physical[1],
                                label: Physical[1],
                            },
                            {
                                value: Physical[2],
                                label: Physical[2],
                            },
                            {
                                value: Physical[3],
                                label: Physical[3],
                            },
                        ],
                    },
                    {
                        // 生物
                        value: Subjects[5],
                        label: Subjects[5],
                        children: [
                            {
                                value: Biology[0],
                                label: Biology[0],
                            },
                            {
                                value: Biology[2],
                                label: Biology[2],
                            },
                        ],
                    },
                    {
                        // 地理
                        value: Subjects[8],
                        label: Subjects[8],
                        children: [
                            {
                                value: Geography[0],
                                label: Geography[0],
                            },
                            {
                                value: Geography[1],
                                label: Geography[1],
                            },
                        ],
                    },
                    {
                        // 政治
                        value: Subjects[6],
                        label: Subjects[6],
                        children: [
                            {
                                value: Politics[0],
                                label: Politics[0],
                            },
                            {
                                value: Politics[1],
                                label: Politics[1],
                            },
                        ],
                    },
                    {
                        // 历史
                        value: Subjects[7],
                        label: Subjects[7],
                        children: [
                            {
                                value: Histories[0],
                                label: Histories[0],
                            },
                            {
                                value: Histories[1],
                                label: Histories[1],
                            },
                        ],
                    },
                ],
            },
            {
                // 初三
                value: grades1[2],
                label: grades1[2],
                children: [
                    {
                        // 语文
                        value: Subjects[0],
                        label: Subjects[0],
                        children: [
                            {
                                value: Chinese[0],
                                label: Chinese[0],
                            },
                            {
                                value: Chinese[1],
                                label: Chinese[1],
                            },
                        ],
                    },
                    {
                        // 数学
                        value: Subjects[1],
                        label: Subjects[1],
                        children: [
                            {
                                value: Maths[0],
                                label: Maths[0],
                            },
                            {
                                value: Maths[1],
                                label: Maths[1],
                            },
                            {
                                value: Maths[2],
                                label: Maths[2],
                            },
                            {
                                value: Maths[5],
                                label: Maths[5],
                            },
                        ],
                    },
                    {
                        // 英语
                        value: Subjects[2],
                        label: Subjects[2],
                        children: [
                            {
                                value: English[0],
                                label: English[0],
                            },
                            {
                                value: English[1],
                                label: English[1],
                            },
                            {
                                value: English[2],
                                label: English[2],
                            },
                            {
                                value: English[3],
                                label: English[3],
                            },
                            {
                                value: English[4],
                                label: English[4],
                            },
                        ],
                    },
                    {
                        // 物理
                        value: Subjects[3],
                        label: Subjects[3],
                        children: [
                            {
                                value: Physical[0],
                                label: Physical[0],
                            },
                            {
                                value: Physical[1],
                                label: Physical[1],
                            },
                            {
                                value: Physical[2],
                                label: Physical[2],
                            },
                            {
                                value: Physical[3],
                                label: Physical[3],
                            },
                            {
                                value: Physical[4],
                                label: Physical[4],
                            },
                        ],
                    },
                    {
                        // 化学
                        value: Subjects[4],
                        label: Subjects[4],
                        children: [
                            {
                                value: Chemistry[1],
                                label: Chemistry[1],
                            },
                            {
                                value: Chemistry[0],
                                label: Chemistry[0],
                            },
                        ],
                    },
                    {
                        // 政治
                        value: Subjects[6],
                        label: Subjects[6],
                        children: [
                            {
                                value: Politics[0],
                                label: Politics[0],
                            },
                            {
                                value: Politics[1],
                                label: Politics[1],
                            },
                            {
                                value: Politics[2],
                                label: Politics[2],
                            },
                        ],
                    },
                    {
                        // 历史
                        value: Subjects[7],
                        label: Subjects[7],
                        children: [
                            {
                                value: Histories[0],
                                label: Histories[0],
                            },
                            {
                                value: Histories[1],
                                label: Histories[1],
                            },
                            {
                                value: Histories[2],
                                label: Histories[2],
                            },
                        ],
                    },
                ],
            },
        ],
    },
    //   高中
    {
        value: levels[2],
        label: levels[2],
        children: [
            {
                // 高一
                value: grades1[0],
                label: grades1[0],
                children: [
                    {
                        // 语文
                        value: Subjects[0],
                        label: Subjects[0],
                        children: [
                            {
                                value: Chinese[0],
                                label: Chinese[0],
                            },
                            {
                                value: Chinese[2],
                                label: Chinese[2],
                            },
                            {
                                value: Chinese[1],
                                label: Chinese[1],
                            },
                        ],
                    },
                    {
                        // 数学
                        value: Subjects[1],
                        label: Subjects[1],
                        children: [
                            {
                                value: Maths[0],
                                label: Maths[0],
                            },
                            {
                                value: Maths[1],
                                label: Maths[1],
                            },
                            {
                                value: Maths[2],
                                label: Maths[2],
                            },
                            {
                                value: Maths[3],
                                label: Maths[3],
                            },
                        ],
                    },
                    {
                        // 英语
                        value: Subjects[2],
                        label: Subjects[2],
                        children: [
                            {
                                value: English[0],
                                label: English[0],
                            },
                            {
                                value: English[1],
                                label: English[1],
                            },
                            {
                                value: English[2],
                                label: English[2],
                            },
                            {
                                value: English[3],
                                label: English[3],
                            },
                        ],
                    },
                    {
                        // 物理
                        value: Subjects[3],
                        label: Subjects[3],
                        children: [
                            {
                                value: Physical[0],
                                label: Physical[0],
                            },
                            {
                                value: Physical[1],
                                label: Physical[1],
                            },
                            {
                                value: Physical[2],
                                label: Physical[2],
                            },
                            {
                                value: Physical[3],
                                label: Physical[3],
                            },
                            {
                                value: Physical[4],
                                label: Physical[4],
                            },
                        ],
                    },
                    {
                        // 化学
                        value: Subjects[4],
                        label: Subjects[4],
                        children: [
                            {
                                value: Chemistry[1],
                                label: Chemistry[1],
                            },
                            {
                                value: Chemistry[0],
                                label: Chemistry[0],
                            },
                            {
                                value: Chemistry[2],
                                label: Chemistry[2],
                            },
                        ],
                    },
                    {
                        // 生物
                        value: Subjects[5],
                        label: Subjects[5],
                        children: [
                            {
                                value: Biology[0],
                                label: Biology[0],
                            },
                            {
                                value: Biology[1],
                                label: Biology[1],
                            },
                            {
                                value: Biology[2],
                                label: Biology[2],
                            },
                        ],
                    },
                    {
                        // 政治
                        value: Subjects[6],
                        label: Subjects[6],
                        children: [
                            {
                                value: Politics[0],
                                label: Politics[0],
                            },
                            {
                                value: Politics[1],
                                label: Politics[1],
                            },
                            {
                                value: Politics[2],
                                label: Politics[2],
                            },
                        ],
                    },
                    {
                        // 历史
                        value: Subjects[7],
                        label: Subjects[7],
                        children: [
                            {
                                value: Histories[0],
                                label: Histories[0],
                            },
                            {
                                value: Histories[1],
                                label: Histories[1],
                            },
                            {
                                value: Histories[2],
                                label: Histories[2],
                            },
                        ],
                    },
                    {
                        // 地理
                        value: Subjects[8],
                        label: Subjects[8],
                        children: [
                            {
                                value: Geography[0],
                                label: Geography[0],
                            },
                            {
                                value: Geography[1],
                                label: Geography[1],
                            },
                            {
                                value: Geography[2],
                                label: Geography[2],
                            },
                        ],
                    },
                ],
            },
            {
                // 高二
                value: grades1[1],
                label: grades1[1],
                children: [
                    {
                        // 语文
                        value: Subjects[0],
                        label: Subjects[0],
                        children: [
                            {
                                value: Chinese[0],
                                label: Chinese[0],
                            },
                            {
                                value: Chinese[2],
                                label: Chinese[2],
                            },
                            {
                                value: Chinese[1],
                                label: Chinese[1],
                            },
                        ],
                    },
                    {
                        // 数学
                        value: Subjects[1],
                        label: Subjects[1],
                        children: [
                            {
                                value: Maths[0],
                                label: Maths[0],
                            },
                            {
                                value: Maths[1],
                                label: Maths[1],
                            },
                            {
                                value: Maths[2],
                                label: Maths[2],
                            },
                            {
                                value: Maths[3],
                                label: Maths[3],
                            },
                            {
                                value: Maths[4],
                                label: Maths[4],
                            },
                            {
                                value: Maths[5],
                                label: Maths[5],
                            },
                        ],
                    },
                    {
                        // 英语
                        value: Subjects[2],
                        label: Subjects[2],
                        children: [
                            {
                                value: English[0],
                                label: English[0],
                            },
                            {
                                value: English[1],
                                label: English[1],
                            },
                            {
                                value: English[2],
                                label: English[2],
                            },
                            {
                                value: English[3],
                                label: English[3],
                            },
                        ],
                    },
                    {
                        // 物理
                        value: Subjects[3],
                        label: Subjects[3],
                        children: [
                            {
                                value: Physical[0],
                                label: Physical[0],
                            },
                            {
                                value: Physical[1],
                                label: Physical[1],
                            },
                            {
                                value: Physical[2],
                                label: Physical[2],
                            },
                            {
                                value: Physical[3],
                                label: Physical[3],
                            },
                            {
                                value: Physical[4],
                                label: Physical[4],
                            },
                        ],
                    },
                    {
                        // 化学
                        value: Subjects[4],
                        label: Subjects[4],
                        children: [
                            {
                                value: Chemistry[1],
                                label: Chemistry[1],
                            },
                            {
                                value: Chemistry[0],
                                label: Chemistry[0],
                            },
                            {
                                value: Chemistry[2],
                                label: Chemistry[2],
                            },
                            {
                                value: Chemistry[3],
                                label: Chemistry[3],
                            },
                        ],
                    },
                    {
                        // 生物
                        value: Subjects[5],
                        label: Subjects[5],
                        children: [
                            {
                                value: Biology[0],
                                label: Biology[0],
                            },
                            {
                                value: Biology[1],
                                label: Biology[1],
                            },
                            {
                                value: Biology[2],
                                label: Biology[2],
                            },
                        ],
                    },
                    {
                        // 政治
                        value: Subjects[6],
                        label: Subjects[6],
                        children: [
                            {
                                value: Politics[0],
                                label: Politics[0],
                            },
                            {
                                value: Politics[1],
                                label: Politics[1],
                            },
                            {
                                value: Politics[2],
                                label: Politics[2],
                            },
                        ],
                    },
                    {
                        // 历史
                        value: Subjects[7],
                        label: Subjects[7],
                        children: [
                            {
                                value: Histories[0],
                                label: Histories[0],
                            },
                            {
                                value: Histories[1],
                                label: Histories[1],
                            },
                            {
                                value: Histories[2],
                                label: Histories[2],
                            },
                        ],
                    },
                    {
                        // 地理
                        value: Subjects[8],
                        label: Subjects[8],
                        children: [
                            {
                                value: Geography[0],
                                label: Geography[0],
                            },
                            {
                                value: Geography[1],
                                label: Geography[1],
                            },
                            {
                                value: Geography[2],
                                label: Geography[2],
                            },
                        ],
                    },
                ],
            },
            {
                // 高三
                value: grades1[2],
                label: grades1[2],
                children: [
                    {
                        // 语文
                        value: Subjects[0],
                        label: Subjects[0],
                        children: [
                            {
                                value: Chinese[0],
                                label: Chinese[0],
                            },
                            {
                                value: Chinese[2],
                                label: Chinese[2],
                            },
                            {
                                value: Chinese[1],
                                label: Chinese[1],
                            },
                        ],
                    },
                    {
                        // 数学
                        value: Subjects[1],
                        label: Subjects[1],
                        children: [
                            {
                                value: Maths[0],
                                label: Maths[0],
                            },
                            {
                                value: Maths[1],
                                label: Maths[1],
                            },
                            {
                                value: Maths[2],
                                label: Maths[2],
                            },
                            {
                                value: Maths[3],
                                label: Maths[3],
                            },
                            {
                                value: Maths[4],
                                label: Maths[4],
                            },
                            {
                                value: Maths[5],
                                label: Maths[5],
                            },
                        ],
                    },
                    {
                        // 英语
                        value: Subjects[2],
                        label: Subjects[2],
                        children: [
                            {
                                value: English[0],
                                label: English[0],
                            },
                            {
                                value: English[1],
                                label: English[1],
                            },
                            {
                                value: English[2],
                                label: English[2],
                            },
                            {
                                value: English[3],
                                label: English[3],
                            },
                        ],
                    },
                    {
                        // 物理
                        value: Subjects[3],
                        label: Subjects[3],
                        children: [
                            {
                                value: Physical[0],
                                label: Physical[0],
                            },
                            {
                                value: Physical[1],
                                label: Physical[1],
                            },
                            {
                                value: Physical[2],
                                label: Physical[2],
                            },
                            {
                                value: Physical[3],
                                label: Physical[3],
                            },
                            {
                                value: Physical[4],
                                label: Physical[4],
                            },
                            {
                                value: Physical[5],
                                label: Physical[5],
                            },
                        ],
                    },
                    {
                        // 化学
                        value: Subjects[4],
                        label: Subjects[4],
                        children: [
                            {
                                value: Chemistry[1],
                                label: Chemistry[1],
                            },
                            {
                                value: Chemistry[0],
                                label: Chemistry[0],
                            },
                            {
                                value: Chemistry[2],
                                label: Chemistry[2],
                            },
                            {
                                value: Chemistry[3],
                                label: Chemistry[3],
                            },
                        ],
                    },
                    {
                        // 生物
                        value: Subjects[5],
                        label: Subjects[5],
                        children: [
                            {
                                value: Biology[0],
                                label: Biology[0],
                            },
                            {
                                value: Biology[1],
                                label: Biology[1],
                            },
                            {
                                value: Biology[2],
                                label: Biology[2],
                            },
                        ],
                    },
                    {
                        // 政治
                        value: Subjects[6],
                        label: Subjects[6],
                        children: [
                            {
                                value: Politics[0],
                                label: Politics[0],
                            },
                            {
                                value: Politics[1],
                                label: Politics[1],
                            },
                            {
                                value: Politics[2],
                                label: Politics[2],
                            },
                        ],
                    },
                    {
                        // 历史
                        value: Subjects[7],
                        label: Subjects[7],
                        children: [
                            {
                                value: Histories[0],
                                label: Histories[0],
                            },
                            {
                                value: Histories[1],
                                label: Histories[1],
                            },
                            {
                                value: Histories[2],
                                label: Histories[2],
                            },
                        ],
                    },
                    {
                        // 地理
                        value: Subjects[8],
                        label: Subjects[8],
                        children: [
                            {
                                value: Geography[0],
                                label: Geography[0],
                            },
                            {
                                value: Geography[1],
                                label: Geography[1],
                            },
                            {
                                value: Geography[2],
                                label: Geography[2],
                            },
                        ],
                    },
                ],
            },
        ],
    },
    //   大学
    {
        value: levels[3],
        label: levels[3],
        children: [
            {
                // 高数
                value: advancedSubjects[0],
                label: advancedSubjects[0],
                children: [
                    {
                        value: advancedMath[0],
                        label: advancedMath[0],
                    },
                    {
                        value: advancedMath[1],
                        label: advancedMath[1],
                    },
                    {
                        value: advancedMath[2],
                        label: advancedMath[2],
                    },
                    {
                        value: advancedMath[3],
                        label: advancedMath[3],
                    },
                    {
                        value: advancedMath[4],
                        label: advancedMath[4],
                    },
                    {
                        value: advancedMath[5],
                        label: advancedMath[5],
                    },
                ]
            },
            {
                // 线代
                value: advancedSubjects[1],
                label: advancedSubjects[1],
                children: [
                    {
                        value: linearAlgebra[0],
                        label: linearAlgebra[0],
                    },
                    {
                        value: linearAlgebra[1],
                        label: linearAlgebra[1],
                    },
                    {
                        value: linearAlgebra[2],
                        label: linearAlgebra[2],
                    },
                ]
            },
            {
                // 马克思
                value: advancedSubjects[2],
                label: advancedSubjects[2],
                children: [
                    {
                        value: marxism[0],
                        label: marxism[0],
                    },
                    {
                        value: marxism[1],
                        label: marxism[1],
                    },
                    {
                        value: marxism[2],
                        label: marxism[2],
                    },
                ]
            },
            {
                // 大物
                value: advancedSubjects[3],
                label: advancedSubjects[3],
                children: [
                    {
                        value: advancedPhysics[0],
                        label: advancedPhysics[0],
                    },
                    {
                        value: advancedPhysics[1],
                        label: advancedPhysics[1],
                    },
                    {
                        value: advancedPhysics[2],
                        label: advancedPhysics[2],
                    },
                    {
                        value: advancedPhysics[3],
                        label: advancedPhysics[3],
                    },
                    {
                        value: advancedPhysics[4],
                        label: advancedPhysics[4],
                    },
                    {
                        value: advancedPhysics[5],
                        label: advancedPhysics[5],
                    },
                    {
                        value: advancedPhysics[6],
                        label: advancedPhysics[6],
                    },
                    {
                        value: advancedPhysics[7],
                        label: advancedPhysics[7],
                    },
                ]
            },
        ],
    },
]

const majors = ['网络空间安全', '软件工程', '计算机科学', '人工智能']
const subjects1 = ['计算机组成原理', '计算机网络', '网络安全基础', '网络空间安全导论', '密码学', '网络攻防', '信息论与编码']
const knowledge1 = ['冯诺依曼体系架构', '并行处理', '算术逻辑单元', 'CPU和寄存器', '存储系统', '总线结构',
    '网络分层模型', 'IP和子网', 'TCP/IP和UDP', 'DNS和NAT', 'HTTP和HTTPS', '传输层', '数据链路层',
    '个人隐私保护', '风险评估与管理', '加密技术', '身份认证和访问控制', '安全防护技术',
    '网络安全模型', '密码学基础', '网络安全威胁', '空间合作管理',
    '密码学的定义', '现代密码体制', '哈希函数', '数字签名', '密钥交换协议', '量子密码学',
    '网络攻击手段', '网络防御手段', '网络扫描技术', 'SQL注入攻击', 'DOS和DDOS', 'XSS和CSRF',
    '信息熵', '信道容量', '算术编码']

const subjects2 = ['数据结构与算法', '离散数学', 'python程序设计', '面向对象编程', '软件方法论', '机器学习']
const knowledge2 = ['数组和链表', '队列和栈', '树和图', '递归和分治算法', '排序算法', '搜索算法', '图论', '动态规划',
    '集合论', '关系和函数', '逻辑和布尔代数', '数论',
    '数据类型', '控制结构', '类和方法', '模块和包',
    '类', '构造函数', '继承与多态与封装', '抽象和接口',
    '软件工程的定义', '软件开发的过程', '软件开发的工具', '软件质量保证', '软件工程的原则',
    '监督学习相关', '决策树', '随机森林', '向量机', '卷积神经网络', '人工神经网络', '数据预处理', '伦理道德'
]

const subjects3 = ['操作系统', '数据库原理', '编译原理', '程序设计基础', '计算机图形学', '分布式系统']
const knowledge3 = ['系统分类', '进程管理', '内存系统', '文件管理',
    '数据模型', '关系型数据库', '非关系型数据库', 'SQL语言', '事务处理', '并发控制',
    '编译器设计', '词法分析', '语法分析', '语义分析',
    '变量和常量', '代码生成', '代码优化', '代码风格', '设计过程分析', '虚拟机',
    '图形与图像', '矩阵计算', '光影处理', '3D图形学', '动画与特效', '游戏编程',
    '分布式系统的定义', '分布式系统的原理', '主流技术', '分布式事务', '中间件', '分布式系统设计模式'
]

const subjects4 = ['模式识别', '深度学习', '自然语言处理', '计算机视觉', '计算智能导论']
const knowledge4 = ['特征提取', '分类算法', '聚类分析', '模式识别系统设计', '统计学习理论',
    '卷积神经网络', '循环神经网络', '长短期记忆网络', '生成对抗网络',
    '词嵌入', '语言模型', '机器翻译', '文本分类', '情感分析',
    '图像处理', '特征检测', '目标识别', '场景重建', '图像分割',
    '遗传算法', '模糊逻辑', '神经模糊系统', '群体智能', '蚁群优化'
]


const buoptions = [
    {
        value: majors[0],
        label: majors[0],
        children: [
            {
                value: subjects1[0],
                label: subjects1[0],
                children: [
                    {
                        value: knowledge1[0],
                        label: knowledge1[0]
                    },
                    {
                        value: knowledge1[1],
                        label: knowledge1[1]
                    },
                    {
                        value: knowledge1[2],
                        label: knowledge1[2]
                    },
                    {
                        value: knowledge1[3],
                        label: knowledge1[3]
                    },
                    {
                        value: knowledge1[4],
                        label: knowledge1[4]
                    },
                    {
                        value: knowledge1[5],
                        label: knowledge1[5]
                    },
                ]
            },
            {
                value: subjects1[1],
                label: subjects1[1],
                children: [
                    {
                        value: knowledge1[6],
                        label: knowledge1[6]
                    },
                    {
                        value: knowledge1[7],
                        label: knowledge1[7]
                    },
                    {
                        value: knowledge1[8],
                        label: knowledge1[8]
                    },
                    {
                        value: knowledge1[9],
                        label: knowledge1[9]
                    },
                    {
                        value: knowledge1[10],
                        label: knowledge1[10]
                    },
                    {
                        value: knowledge1[11],
                        label: knowledge1[11]
                    },
                    {
                        value: knowledge1[12],
                        label: knowledge1[12]
                    },
                ]
            },
            {
                value: subjects1[2],
                label: subjects1[2],
                children: [
                    {
                        value: knowledge1[13],
                        label: knowledge1[13]
                    },
                    {
                        value: knowledge1[14],
                        label: knowledge1[14]
                    },
                    {
                        value: knowledge1[15],
                        label: knowledge1[15]
                    },
                    {
                        value: knowledge1[16],
                        label: knowledge1[16]
                    },
                    {
                        value: knowledge1[17],
                        label: knowledge1[17]
                    },
                ]
            },
            {
                value: subjects1[3],
                label: subjects1[3],
                children: [
                    {
                        value: knowledge1[18],
                        label: knowledge1[18]
                    },
                    {
                        value: knowledge1[19],
                        label: knowledge1[19]
                    },
                    {
                        value: knowledge1[20],
                        label: knowledge1[20]
                    },
                    {
                        value: knowledge1[21],
                        label: knowledge1[21]
                    },
                ]
            },
            {
                value: subjects1[4],
                label: subjects1[4],
                children: [
                    {
                        value: knowledge1[22],
                        label: knowledge1[22]
                    },
                    {
                        value: knowledge1[23],
                        label: knowledge1[23]
                    },
                    {
                        value: knowledge1[24],
                        label: knowledge1[24]
                    },
                    {
                        value: knowledge1[25],
                        label: knowledge1[25]
                    },
                    {
                        value: knowledge1[26],
                        label: knowledge1[26]
                    },
                    {
                        value: knowledge1[27],
                        label: knowledge1[27]
                    },
                ]
            },
            {
                value: subjects1[5],
                label: subjects1[5],
                children: [
                    {
                        value: knowledge1[28],
                        label: knowledge1[28]
                    },
                    {
                        value: knowledge1[29],
                        label: knowledge1[29]
                    },
                    {
                        value: knowledge1[30],
                        label: knowledge1[30]
                    },
                    {
                        value: knowledge1[31],
                        label: knowledge1[31]
                    },
                    {
                        value: knowledge1[32],
                        label: knowledge1[32]
                    },
                    {
                        value: knowledge1[33],
                        label: knowledge1[33]
                    },
                ]
            },
            {
                value: subjects1[6],
                label: subjects1[6],
                children: [
                    {
                        value: knowledge1[34],
                        label: knowledge1[34]
                    },
                    {
                        value: knowledge1[35],
                        label: knowledge1[35]
                    },
                    {
                        value: knowledge1[36],
                        label: knowledge1[36]
                    },
                ]
            },
        ]
    },
    {
        value: majors[1],
        label: majors[1],
        children: [
            {
                value: subjects2[0],
                label: subjects2[0],
                children: [
                    {
                        value: knowledge2[0],
                        label: knowledge2[0]
                    },
                    {
                        value: knowledge2[1],
                        label: knowledge2[1]
                    },
                    {
                        value: knowledge2[2],
                        label: knowledge2[2]
                    },
                    {
                        value: knowledge2[3],
                        label: knowledge2[3]
                    },
                    {
                        value: knowledge2[4],
                        label: knowledge2[4]
                    },
                    {
                        value: knowledge2[5],
                        label: knowledge2[5]
                    },
                    {
                        value: knowledge2[6],
                        label: knowledge2[6]
                    },
                    {
                        value: knowledge2[7],
                        label: knowledge2[7]
                    },
                ]
            },
            {
                value: subjects2[1],
                label: subjects2[1],
                children: [
                    {
                        value: knowledge2[8],
                        label: knowledge2[8]
                    },
                    {
                        value: knowledge2[9],
                        label: knowledge2[9]
                    },
                    {
                        value: knowledge2[10],
                        label: knowledge2[10]
                    },
                    {
                        value: knowledge2[11],
                        label: knowledge2[11]
                    },
                ]
            },
            {
                value: subjects2[2],
                label: subjects2[2],
                children: [
                    {
                        value: knowledge2[12],
                        label: knowledge2[12]
                    },
                    {
                        value: knowledge2[13],
                        label: knowledge2[13]
                    },
                    {
                        value: knowledge2[14],
                        label: knowledge2[14]
                    },
                    {
                        value: knowledge2[15],
                        label: knowledge2[15]
                    },
                ]
            },
            {
                value: subjects2[3],
                label: subjects2[3],
                children: [
                    {
                        value: knowledge2[16],
                        label: knowledge2[16]
                    },
                    {
                        value: knowledge2[17],
                        label: knowledge2[17]
                    },
                    {
                        value: knowledge2[18],
                        label: knowledge2[18]
                    },
                    {
                        value: knowledge2[19],
                        label: knowledge2[19]
                    },
                ]
            },
            {
                value: subjects2[4],
                label: subjects2[4],
                children: [
                    {
                        value: knowledge2[20],
                        label: knowledge2[20]
                    },
                    {
                        value: knowledge2[21],
                        label: knowledge2[21]
                    },
                    {
                        value: knowledge2[22],
                        label: knowledge2[22]
                    },
                    {
                        value: knowledge2[23],
                        label: knowledge2[23]
                    },
                    {
                        value: knowledge2[24],
                        label: knowledge2[24]
                    },
                ]
            },
            {
                value: subjects2[5],
                label: subjects2[5],
                children: [
                    {
                        value: knowledge2[25],
                        label: knowledge2[25]
                    },
                    {
                        value: knowledge2[26],
                        label: knowledge2[26]
                    },
                    {
                        value: knowledge2[27],
                        label: knowledge2[27]
                    },
                    {
                        value: knowledge2[28],
                        label: knowledge2[28]
                    },
                    {
                        value: knowledge2[29],
                        label: knowledge2[29]
                    },
                    {
                        value: knowledge2[30],
                        label: knowledge2[30]
                    },
                    {
                        value: knowledge2[31],
                        label: knowledge2[31]
                    },
                    {
                        value: knowledge2[32],
                        label: knowledge2[32]
                    },
                ]
            },
        ]
    },
    {
        value: majors[2],
        label: majors[2],
        children: [
            {
                value: subjects3[0],
                label: subjects3[0],
                children: [
                    {
                        value: knowledge3[0],
                        label: knowledge3[0]
                    },
                    {
                        value: knowledge3[1],
                        label: knowledge3[1]
                    },
                    {
                        value: knowledge3[2],
                        label: knowledge3[2]
                    },
                    {
                        value: knowledge3[3],
                        label: knowledge3[3]
                    },
                ]
            },
            {
                value: subjects3[1],
                label: subjects3[1],
                children: [
                    {
                        value: knowledge3[4],
                        label: knowledge3[4]
                    },
                    {
                        value: knowledge3[5],
                        label: knowledge3[5]
                    },
                    {
                        value: knowledge3[6],
                        label: knowledge3[6]
                    },
                    {
                        value: knowledge3[7],
                        label: knowledge3[7]
                    },
                    {
                        value: knowledge3[8],
                        label: knowledge3[8]
                    },
                    {
                        value: knowledge3[9],
                        label: knowledge3[9]
                    },
                ]
            },
            {
                value: subjects3[2],
                label: subjects3[2],
                children: [
                    {
                        value: knowledge3[10],
                        label: knowledge3[10]
                    },
                    {
                        value: knowledge3[11],
                        label: knowledge3[11]
                    },
                    {
                        value: knowledge3[12],
                        label: knowledge3[12]
                    },
                    {
                        value: knowledge3[13],
                        label: knowledge3[13]
                    },
                ]
            },
            {
                value: subjects3[3],
                label: subjects3[3],
                children: [
                    {
                        value: knowledge3[14],
                        label: knowledge3[14]
                    },
                    {
                        value: knowledge3[15],
                        label: knowledge3[15]
                    },
                    {
                        value: knowledge3[16],
                        label: knowledge3[16]
                    },
                    {
                        value: knowledge3[17],
                        label: knowledge3[17]
                    },
                    {
                        value: knowledge3[18],
                        label: knowledge3[18]
                    },
                    {
                        value: knowledge3[19],
                        label: knowledge3[19]
                    },
                ]
            },
            {
                value: subjects3[4],
                label: subjects3[4],
                children: [
                    {
                        value: knowledge3[20],
                        label: knowledge3[20]
                    },
                    {
                        value: knowledge3[21],
                        label: knowledge3[21]
                    },
                    {
                        value: knowledge3[22],
                        label: knowledge3[22]
                    },
                    {
                        value: knowledge3[23],
                        label: knowledge3[23]
                    },
                    {
                        value: knowledge3[24],
                        label: knowledge3[24]
                    },
                    {
                        value: knowledge3[25],
                        label: knowledge3[25]
                    },
                ]
            },
            {
                value: subjects3[5],
                label: subjects3[5],
                children: [
                    {
                        value: knowledge3[26],
                        label: knowledge3[26]
                    },
                    {
                        value: knowledge3[27],
                        label: knowledge3[27]
                    },
                    {
                        value: knowledge3[28],
                        label: knowledge3[28]
                    },
                    {
                        value: knowledge3[29],
                        label: knowledge3[29]
                    },
                    {
                        value: knowledge3[30],
                        label: knowledge3[30]
                    },
                    {
                        value: knowledge3[31],
                        label: knowledge3[31]
                    },
                ]
            },
        ]
    },
    {
        value: majors[3],
        label: majors[3],
        children: [
            {
                value: subjects4[0],
                label: subjects4[0],
                children: [
                    {
                        value: knowledge4[0],
                        label: knowledge4[0]
                    },
                    {
                        value: knowledge4[1],
                        label: knowledge4[1]
                    },
                    {
                        value: knowledge4[2],
                        label: knowledge4[2]
                    },
                    {
                        value: knowledge4[3],
                        label: knowledge4[3]
                    },
                    {
                        value: knowledge4[4],
                        label: knowledge4[4]
                    },
                ]
            },
            {
                value: subjects4[1],
                label: subjects4[1],
                children: [
                    {
                        value: knowledge4[5],
                        label: knowledge4[5]
                    },
                    {
                        value: knowledge4[6],
                        label: knowledge4[6]
                    },
                    {
                        value: knowledge4[7],
                        label: knowledge4[7]
                    },
                    {
                        value: knowledge4[8],
                        label: knowledge4[8]
                    },
                ]
            },
            {
                value: subjects4[2],
                label: subjects4[2],
                children: [
                    {
                        value: knowledge4[9],
                        label: knowledge4[9]
                    },
                    {
                        value: knowledge4[10],
                        label: knowledge4[10]
                    },
                    {
                        value: knowledge4[11],
                        label: knowledge4[11]
                    },
                    {
                        value: knowledge4[12],
                        label: knowledge4[12]
                    },
                    {
                        value: knowledge4[13],
                        label: knowledge4[13]
                    },
                ]
            },
            {
                value: subjects4[3],
                label: subjects4[3],
                children: [
                    {
                        value: knowledge4[14],
                        label: knowledge4[14]
                    },
                    {
                        value: knowledge4[15],
                        label: knowledge4[15]
                    },
                    {
                        value: knowledge4[16],
                        label: knowledge4[16]
                    },
                    {
                        value: knowledge4[17],
                        label: knowledge4[17]
                    },
                    {
                        value: knowledge4[18],
                        label: knowledge4[18]
                    },
                ]
            },
            {
                value: subjects4[4],
                label: subjects4[4],
                children: [
                    {
                        value: knowledge4[19],
                        label: knowledge4[19]
                    },
                    {
                        value: knowledge4[20],
                        label: knowledge4[20]
                    },
                    {
                        value: knowledge4[21],
                        label: knowledge4[21]
                    },
                    {
                        value: knowledge4[22],
                        label: knowledge4[22]
                    },
                    {
                        value: knowledge4[23],
                        label: knowledge4[23]
                    },
                ]
            },
        ]
    },
]
export {
    topics,
    options,
    buoptions
}