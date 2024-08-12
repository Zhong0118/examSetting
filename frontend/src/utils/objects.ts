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


export {
    topics,
    options
}