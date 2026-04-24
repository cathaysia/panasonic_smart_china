DRYER_OPTION_LABELS = {
    "drySpend": {
        1: "1 级",
        2: "2 级",
        3: "3 级",
        4: "4 级",
        5: "5 级",
    },
    "dryMode": {
        1: "熨衣",
        2: "即穿",
        3: "入柜",
        4: "暖衣",
    },
    "dryTemp": {
        1: "40°C",
        2: "45°C",
        3: "50°C",
        4: "55°C",
        5: "60°C",
        6: "65°C",
    },
    "airVo": {
        1: "1 档",
        2: "2 档",
        3: "3 档",
    },
    "dryType": {
        1: "低温烘干",
        2: "节能",
        3: "快速",
    },
    "freshenSetTime": {
        0: "关",
        2: "2 小时",
        3: "3 小时",
        4: "4 小时",
        5: "5 小时",
        6: "6 小时",
        7: "7 小时",
        8: "8 小时",
        9: "9 小时",
        10: "10 小时",
    },
}

DRYER_SELECT_FIELDS = [
    ("drySpend", "干衣度", [1, 2, 3, 4, 5]),
    ("dryMode", "干衣模式", [1, 2, 3, 4]),
    ("dryTemp", "干衣温度", [1, 2, 3, 4, 5, 6]),
    ("airVo", "风量", [1, 2, 3]),
    ("dryType", "干衣类型", [1, 2, 3]),
]

DRYER_NUMBER_FIELDS = [
    ("timeDelayTotal", "预约时长", 0, 24, 1, "h"),
    ("dryTime", "干衣时间", 0, 240, 1, "min"),
    ("freshenSetTime", "清新保持", 0, 10, 1, "h"),
]

DRYER_SWITCH_FIELDS = [
    ("easyIroning", "免熨烫"),
    ("mute", "免打扰"),
    ("delayClothes", "延时添衣"),
]
