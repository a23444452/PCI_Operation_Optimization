"""All configurations: connection strings, defect mappings, customer specs."""

# ============================================================
# Database connections
# ============================================================
PPDA_CONN = "oracle+oracledb://training:training@tcf15orc302a-scan.corning.com:1521/?service_name=TC_PPDA.WORLD"

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
ADOMD_DLL_PATH = r"C:\Users\wangm44"

# ============================================================
# Tanks to process (for SOLID density)
# ============================================================
TANKS_TO_PROCESS = [
    "TC10", "TC12", "TC13", "TC14",
    "TC17", "TC18", "TC19", "TC20", "TC21",
]

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
    "crate_id", "Gen",
    "A-Crack", "A-Drip", "A-ADG", "A-SC", "A-Stain",
    "B-Drip", "B-Stain", "B-SC", "B-Crack", "B-ADG",
    "Full Sheet Broken",
]


# ============================================================
# Customer (Receiver) spec rules
# ============================================================
RECEIVER_SPECS = {
    # ---- HF ----
    "HF_Gen6_0.4t":{
            "blister100": {"type": "Blister",         "min_size": 100},
            "npt100":     {"type": "Needle Pt",       "min_size": 100},
            "pt100":      {"type": "Platinum",        "min_size": 100},
            "cpt100":     {"type": "Crystalline Pt", "min_size": 100},
            "sbl100":     {"type": "Surface Blister", "min_size": 100},
            "zr100":      {"type": "Zr",              "min_size": 100},
    },
    "HF_Gen8.6_0.4t":{
            "blister700": {"type": "Blister",         "min_size": 700},
            "npt300":     {"type": "Needle Pt",       "min_size": 300},
            "pt100":      {"type": "Platinum",        "min_size": 100},
            "cpt100":     {"type": "Crystalline Pt", "min_size": 100},
            "sbl100":     {"type": "Surface Blister", "min_size": 100},
            "zr100":      {"type": "Zr",              "min_size": 100},
    },
    "HF_Gen8.6_0.485t":{
            "blister500": {"type": "Blister",         "min_size": 500},
            "npt300":     {"type": "Needle Pt",       "min_size": 300},
            "pt50":      {"type": "Platinum",        "min_size": 50},
            "cpt40":     {"type": "Crystalline Pt", "min_size": 40},
            "sbl100":     {"type": "Surface Blister", "min_size": 100},
            "zr100":      {"type": "Zr",              "min_size": 100},
    },
    
    # ---- BJ ----
    "BJ_Gen8.5_0.4t":{
            "blister300": {"type": "Blister",         "min_size": 300},
            "npt100":     {"type": "Needle Pt",       "min_size": 100},
            "pt100":      {"type": "Platinum",        "min_size": 100},
            "cpt100":     {"type": "Crystalline Pt", "min_size": 100},
            "sbl100":     {"type": "Surface Blister", "min_size": 100},
            "zr100":      {"type": "Zr",              "min_size": 100},
    },
    "BJ_Gen8.5_0.5t":{
            "blister300": {"type": "Blister",         "min_size": 300},
            "npt100":     {"type": "Needle Pt",       "min_size": 100},
            "pt100":      {"type": "Platinum",        "min_size": 100},
            "cpt100":     {"type": "Crystalline Pt", "min_size": 100},
            "sbl100":     {"type": "Surface Blister", "min_size": 100},
            "zr100":      {"type": "Zr",              "min_size": 100},
    },
   
    # ---- MY ----
    "MY_Gen8.6_0.4t":{
            "blister500": {"type": "Blister",         "min_size": 500},
            "npt300":     {"type": "Needle Pt",       "min_size": 300},
            "pt100":      {"type": "Platinum",        "min_size": 100},
            "cpt100":     {"type": "Crystalline Pt", "min_size": 100},
            "sbl100":     {"type": "Surface Blister", "min_size": 100},
            "zr100":      {"type": "Zr",              "min_size": 100},
    },    
    # ---- XY ----
    "XY_Gen8.6_0.485t":{
            "blister300": {"type": "Blister",         "min_size": 300},
            "npt300":     {"type": "Needle Pt",       "min_size": 300},
            "pt50":      {"type": "Platinum",        "min_size": 50},
            "cpt40":     {"type": "Crystalline Pt", "min_size": 40},
            "sbl100":     {"type": "Surface Blister", "min_size": 100},
            "zr100":      {"type": "Zr",              "min_size": 100},
    },       
    # ---- CD ----
    "CD_Gen8.7_0.38t":{
            "blister300": {"type": "Blister",         "min_size": 300},
            "npt100":     {"type": "Needle Pt",       "min_size": 100},
            "pt100":      {"type": "Platinum",        "min_size": 100},
            "cpt100":     {"type": "Crystalline Pt", "min_size": 100},
            "sbl100":     {"type": "Surface Blister", "min_size": 100},
            "zr100":      {"type": "Zr",              "min_size": 100},
    },
    "CD_Gen8.7_0.4t":{
            "blister300": {"type": "Blister",         "min_size": 300},
            "npt300":     {"type": "Needle Pt",       "min_size": 300},
            "pt100":      {"type": "Platinum",        "min_size": 100},
            "cpt100":     {"type": "Crystalline Pt", "min_size": 100},
            "sbl100":     {"type": "Surface Blister", "min_size": 100},
            "zr100":      {"type": "Zr",              "min_size": 100},
    }
}


COMPOSITE_COLUMNS = {
    "NG(Pt_CPt_SD)<6%": ["blister", "other", "sbl", "npt", "pt", "cpt"],
    "ADG":              ["A-ADG", "B-ADG"],     # 直接列欄位名
}



RECEIVER_OUTPUT_ORDER = [
    "crate_id", "Gen", "crate_id"
    "blister100", "blister300", "blister500", "blister700",
    "npt100", "npt300", "pt50", "pt100",
    "cpt40", "cpt100", "sbl100", "zr100",
    "in_qty", "crBIS",
    "A-Crack", "A-Drip", "A-ADG", "A-SC", "A-Stain",
    "B-Drip", "B-Stain", "B-SC", "B-Crack", "B-ADG",
    "Full Sheet Broken",
    "NG(Pt_CPt_SD)<6%", "ADG",
]


GENERAL_OUTPUT_ORDER = [
    "crate_id", "in_qty", "crBIS",
    "Blister", "Needle Pt", "Platinum", "Crystalline Pt",
    "Surface Blister", "Zr", "Other",
    "A-Crack", "A-Drip", "A-ADG", "A-SC", "A-Stain",
    "B-Drip", "B-Stain", "B-SC", "B-Crack", "B-ADG",
    "Full Sheet Broken",
    "ADG",
]

# ============================================================
# Attribute pipeline configuration
# ============================================================

# Attribute query process (MES or Juno)
ATTRIBUTE_PROCESS = "MES"

# Process-specific stress table settings (Juno uses different column names)
PROCESS_CONFIG = {
    "MES": {
        "stress_table": "ONEMES.PPT_QC_AREA_STRESS_SUMM",
        "tank_col":     "TANK_ID",
        "time_col":     "SAMPLE_TS",
        "mrv_col":      "MAX_MRV",
    },
    "Juno": {
        "stress_table": "IWMES.BOD_TBLQCAREASTRESSSUMM",
        "tank_col":     "TANKID",
        "time_col":     "SAMPLETS",
        "mrv_col":      "MRV_TRANSMISSION_MAX",
    },
}

QUALITY_LONG_TABLE = "IWMES.DIMES_PPTU_PT_CRATEAUDIT"
EDGE_GRAD_TABLE    = "ONEMES.PPT_QC_FSW_EDGE_GRAD_SUMM"

ORACLE_IN_BATCH_SIZE = 1000


# ITM_NAME items to fetch (aligned with M codes)
ATTR_REQUIRED_ITMS = [
    "PRODUCT_CODE",
    "CUT_SHEET_SIZE", "CRATE_CODE", "START_TIME", "END_TIME",
    "QUANTITY", "THICKNESS_MM",
    "MAX_THICKNESS", "MIN_THICKNESS", "AVG_THICKNESS", "RNG_THICKNESS",
    "750MM_MWRNG_MAX", "620MM_MWRNG_MAX",
    "150MM_MWRNG_MAX", "75MM_MWRNG_MAX",
    "50MM_MWRNG_MAX", "25MM_MWRNG_MAX",
    "FEELER_GAGE_MAX", "CRI_MAX_RNG", "CRI_MAX_ABSMAX",
    "WAVINESS_.8_08_MAX", "WAVINESS_.8_25_MAX", "CORD_CONTRAST_MAX",
    "MAXFSWARP", "EDGE_GRAD_MAX", "EDGE_GRAD_CORNER",
    "MAXFSWARP_R", "EDGE_GRAD_MAX_R", "EDGE_GRAD_CORNER_R",
]

ATTR_RENAME_MAP = {
    "MAXFSWARP":            "BOW_RANGE",
    "EDGE_GRAD_MAX":        "BOW_EDGE_GRAD_MAX",
    "EDGE_GRAD_CORNER":     "BOW_CORNER_GRAD_MAX",
    "MAXFSWARP_R":          "BOW_RANGE_B",
    "EDGE_GRAD_MAX_R":      "BOW_EDGE_GRAD_MAX_B",
    "EDGE_GRAD_CORNER_R":   "BOW_CORNER_GRAD_MAX_B",
}

ATTR_NUMERIC_COLUMNS = [
    "BOW_EDGE_GRAD_MAX", "BOW_CORNER_GRAD_MAX",
    "BOW_EDGE_GRAD_MAX_B", "BOW_CORNER_GRAD_MAX_B",
    "MAX_THICKNESS", "MIN_THICKNESS", "AVG_THICKNESS", "RNG_THICKNESS",
    "750MM_MWRNG_MAX", "620MM_MWRNG_MAX",
    "150MM_MWRNG_MAX", "75MM_MWRNG_MAX",
    "50MM_MWRNG_MAX", "25MM_MWRNG_MAX",
    "WAVINESS_.8_08_MAX", "WAVINESS_.8_25_MAX",
    "CORD_CONTRAST_MAX", "RET_MRV_MAX", "QUANTITY",
]

ATTR_REQUIRED_COLUMNS = [
    "CRATE_ID", "PRODUCT_CODE", "CUT_SHEET_SIZE", "CRATE_CODE",
    "START_TIME", "END_TIME", "QUANTITY", "THICKNESS_MM",
    "MAX_THICKNESS", "MIN_THICKNESS", "AVG_THICKNESS", "RNG_THICKNESS",
    "750MM_MWRNG_MAX", "620MM_MWRNG_MAX",
    "150MM_MWRNG_MAX", "75MM_MWRNG_MAX",
    "50MM_MWRNG_MAX", "25MM_MWRNG_MAX",
    "BOW_RANGE", "BOW_EDGE_GRAD_MAX", "BOW_CORNER_GRAD_MAX",
    "BOW_RANGE_B", "BOW_EDGE_GRAD_MAX_B", "BOW_CORNER_GRAD_MAX_B",
    "FEELER_GAGE_MAX", "CRI_MAX_RNG", "CRI_MAX_ABSMAX",
    "RET_MRV_MAX",
    "WAVINESS_.8_08_MAX", "WAVINESS_.8_25_MAX", "CORD_CONTRAST_MAX",
]

ATTR_CUSTOMER_COLUMN_ORDER = [
    "FSHEET_HAKY_CODE", "CUT_SHEET_SIZE", "CRATE_CODE",
    "START_TIME", "END_TIME", "FSHEET_CODE", "LINE_CODE",
    "DIRECTION", "STRESS_CODE", "F_LOT_SPLIT", "BOOKING_NO",
    "QUANTITY", "THICKNESS_MM",
    "MAX_THICKNESS", "MIN_THICKNESS", "AVG_THICKNESS", "RNG_THICKNESS",
    "750MM_MWRNG_MAX", "725MM_MWRNG_MAX",
    "620MM_MWRNG_MAX", "555MM_MWRNG_MAX",
    "150MM_MWRNG_MAX", "100MM_MWRNG_MAX",
    "75MM_MWRNG_MAX", "50MM_MWRNG_MAX", "25MM_MWRNG_MAX",
    "BOW_RANGE", "BOW_EDGE_GRAD_MAX", "BOW_CORNER_GRAD_MAX",
    "BOW_RANGE_B", "BOW_EDGE_GRAD_MAX_B", "BOW_CORNER_GRAD_MAX_B",
    "FEELER_GAGE_MAX", "CRI_MAX_RNG", "CRI_MAX_ABSMAX",
    "RET_INT_MAX", "RET_MRV_MAX",
    "WAVINESS_.8_08_MAX", "WAVINESS_.8_25_MAX",
    "CORD_CONTRAST_MAX", "CORD_H3_MAX",
    "INITIAL_ID", "INITIAL_DATE", "LATEST_ID", "LATEST_DATE",
    "B_CURVATURE",
]


# ============================================================
# Shipping Criteria (from Judgement Criteria.xlsx)
# Key = spec name, value = {column: threshold}
# ratio < threshold = compliant; NaN columns omitted (not checked)
# ============================================================
SHIPPING_CRITERIA = {
    "HF_Gen6_0.4t": {
        "blister100": 0.05, "cpt100": 0.05, "npt100": 0.05,
        "pt100": 0.05, "sbl100": 0.05, "zr100": 0.05,
        "ADG": 0.2,
    },
    "BJ_Gen8.5_0.4t": {
        "blister300": 0.06, "cpt100": 0.06, "npt100": 0.06,
        "pt100": 0.06, "sbl100": 0.06, "zr100": 0.06,
        "ADG": 0.2,
    },
    "BJ_Gen8.5_0.5t": {
        "blister300": 0.06, "cpt100": 0.06, "npt100": 0.06,
        "pt100": 0.06, "sbl100": 0.06, "zr100": 0.06,
        "ADG": 0.2,
    },
    "HF_Gen8.6_0.4t": {
        "blister700": 0.06, "cpt100": 0.06, "npt300": 0.06,
        "pt100": 0.06, "sbl100": 0.06, "zr100": 0.06,
        "ADG": 0.2,
    },
    "MY_Gen8.6_0.4t": {
        "blister500": 0.06, "cpt100": 0.06, "npt300": 0.06,
        "pt100": 0.06, "sbl100": 0.06, "zr100": 0.06,
        "NG(Pt_CPt_SD)<6%": 0.06, "ADG": 0.2, "crBIS": 0.08,
    },
    "XY_Gen8.6_0.485t": {
        "blister300": 0.06, "cpt40": 0.06, "npt300": 0.06,
        "pt50": 0.06, "sbl100": 0.06, "zr100": 0.06,
        "NG(Pt_CPt_SD)<6%": 0.06, "ADG": 0.2, "crBIS": 0.08,
    },
    "HF_Gen8.6_0.485t": {
        "blister500": 0.06, "cpt40": 0.06, "npt300": 0.06,
        "pt50": 0.06, "sbl100": 0.06, "zr100": 0.06,
        "ADG": 0.2,
    },
    "CD_Gen8.7_0.38t": {
        "blister300": 0.06, "cpt100": 0.06, "npt100": 0.06,
        "pt100": 0.06, "sbl100": 0.06, "zr100": 0.06,
        "ADG": 0.2,
    },
    "CD_Gen8.7_0.4t": {
        "blister300": 0.06, "cpt100": 0.06, "npt300": 0.06,
        "pt100": 0.06, "sbl100": 0.06, "zr100": 0.06,
        "ADG": 0.2,
    },
}