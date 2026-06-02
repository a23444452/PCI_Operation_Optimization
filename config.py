"""All configurations: connection strings, defect mappings, customer specs."""

# ============================================================
# Database connections
# ============================================================
PPDA_CONN = "oracle+oracledb://training:training@TC_PPDA"

MESDW_CONN = (
    "mssql+pyodbc://TCF11SQL2011/MESDW?"
    "Trusted_Connection=yes&driver=SQL+Server"
)

CUBE_CONN = (
    "Provider=MSOLAP;"
    "Data Source=cgtppd;"
    "Catalog=ppd;"
)

# ADOMD client DLL path (for cube queries)
ADOMD_DLL_PATH = r"C:\Users\linp21"


# ============================================================
# Defect type code -> name mapping
# ============================================================
DEFECT_DICT = {
    0: "Other",
    1: "Blister",
    2: "Silica",
    3: "Platinum",
    4: "Zr",
    5: "Surface Blister",
    6: "Needle Pt",
    7: "Crystalline Pt",
    8: "Open Blister",
}


# ============================================================
# Cube column rename mapping
# ============================================================
CUBE_RENAME = {
    "[Finishing Source Tank].[Mother Crate ID].[Mother Crate ID].[MEMBER_CAPTION]": "crate_id",
    "[FG Product].[FG_Gen].[FG_Gen].[MEMBER_CAPTION]": "Gen",
}

CUBE_DEFECT_COL = "[Defect Tracking].[Defect ID].[Defect ID].[MEMBER_CAPTION]"
CUBE_VALUE_COL  = "[Measures].[F_Defect Loss%]"
CUBE_TIME_COLS  = [
    "[Time Crate].[CR_Time YQMD].[CR_Year].[MEMBER_CAPTION]",
    "[Time Crate].[CR_Time YQMD].[CR_Quarter].[MEMBER_CAPTION]",
    "[Time Crate].[CR_Time YQMD].[CR_Month].[MEMBER_CAPTION]",
]


# ============================================================
# Defect ID short-name mapping (for cube data)
# ============================================================
DEFECT_SHORT_NAMES = {
    "A-side adhered glass full sheet":  "A-ADG",
    "B-side adhered glass full sheet":  "B-ADG",
    "A-side scratch full sheet":        "A-SC",
    "B-side scratch full sheet":        "B-SC",
    "A-side stain full sheet":          "A-Stain",
    "B-side stain full sheet":          "B-Stain",
    "A Full Sheet (Surface) Crack":     "A-Crack",
    "B Full Sheet (Surface) Crack":     "B-Crack",
    "A Side Forming Drips defect":      "A-Drip",
    "B Side Forming Drips defect":      "B-Drip",
    "Crystalline Pt":                   "C-Pt",
    "Surface discontinuity defect":     "SD",
    "Surface Blister":                  "SBL",
}

MSL_COLUMNS = [
    "crate_id",
    "A-Crack", "A-Drip", "A-ADG", "A-SC", "A-Stain",
    "B-Drip", "B-Stain", "B-SC", "B-Crack", "B-ADG",
    "Full Sheet Broken",
]


# ============================================================
# Customer (Receiver) spec rules
# ============================================================
RECEIVER_SPECS = {
    "TC": {
        "blister100": {"type": "Blister",        "min_size": 100},
        "npt100":     {"type": "Needle Pt",      "min_size": 100},
        "pt50":       {"type": "Platinum",       "min_size": 50},
        "cpt40":      {"type": "Crystalline Pt", "min_size": 40},
    },
}


COMPOSITE_COLUMNS = {
    "NG(Pt_CPt_SD)<6%": ["blister", "other", "sbl", "npt", "pt", "cpt"],
    "ADG":              ["A-ADG", "B-ADG"],     # 直接列欄位名
}


RECEIVER_OUTPUT_ORDER = [
    "receiver", "Gen", "crate_id",
    "blister100", "npt100", "pt50", "cpt40", "in_qty",
    "A-Crack", "A-Drip", "A-ADG", "A-SC", "A-Stain",
    "B-Drip", "B-Stain", "B-SC", "B-Crack", "B-ADG",
    "Full Sheet Broken",
    "NG(Pt_CPt_SD)<6%", "ADG",
]