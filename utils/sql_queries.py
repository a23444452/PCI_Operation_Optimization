"""SQL & MDX query templates."""


def build_in_clause(values) -> str:
    """List → 'A','B','C' (with single-quote escaping)."""
    safe = [str(v).replace("'", "''") for v in values]
    return ",".join(f"'{v}'" for v in safe)


# ============================================================
# MESDW: batch / crate / qty / dates
# ============================================================
BATCH_CRATE_SQL = """
SELECT
    Mother_Crate_ID         AS crate_id,
    Tank_ID                 AS tank_id,
    Cut_Lot_ID              AS batch_id,
    Cut_Lot_Start_Date,
    Cut_Lot_End_Date
FROM dbo.CRATE_MES_SUMM
WHERE Cut_Lot_End_Date >= DATEADD(DAY, -1.5, GETDATE())
AND Cut_Lot_ID LIKE 'C%'
AND Mother_Crate_ID LIKE 'TC%'
"""


def build_batch_crate_query(start_date: str, end_date: str) -> str:
    """Parameterized version of BATCH_CRATE_SQL with explicit date range."""
    return f"""
    SELECT
        Mother_Crate_ID         AS crate_id,
        Tank_ID                 AS tank_id,
        Cut_Lot_ID              AS batch_id,
        Cut_Lot_Start_Date,
        Cut_Lot_End_Date
    FROM dbo.CRATE_MES_SUMM
    WHERE Cut_Lot_End_Date >= '{start_date}'
      AND Cut_Lot_End_Date <= '{end_date} 23:59:59'
      AND Cut_Lot_ID LIKE 'C%'
      AND Mother_Crate_ID LIKE 'TC%'
    """


# ============================================================
# PPDA: crate audit (get START_TIME, END_TIME, QUANTITY)
# ============================================================
def build_crate_audit_query(crate_in_clause: str) -> str:
    return f"""
    SELECT CRATE_ID, ITM_NAME, ITM_VALUE1
    FROM IWMES.DIMES_PPTU_PT_CRATEAUDIT
    WHERE CRATE_ID IN ({crate_in_clause})
    AND ITM_NAME IN ('START_TIME', 'END_TIME', 'QUANTITY')
    """


# ============================================================
# PPDA: SOLID inspection (CRBIS)
# ============================================================
def build_crbis_input_query(tank: str, start: str, end: str) -> str:
    return f"""
    SELECT SAMPLE_TS, BATCH_ID, SHEET_ID
    FROM ONEMES.PPT_QC_CRBIS_SUMM
    WHERE TANK_ID = '{tank}'
      AND SAMPLE_TS >= TO_DATE('{start}', 'yyyy-mm-dd HH24:MI')
      AND SAMPLE_TS <= TO_DATE('{end}',   'yyyy-mm-dd HH24:MI')
    """


def build_crbis_defect_query(tank: str, start: str, end: str) -> str:
    return f"""
    SELECT SAMPLE_TS, TANK_ID, DEFECT_TYPE, X_POSITION, Y_POSITION,
           DEFECT_SIZE, DEFECT_JUDGMENT, AJ_DECISION
    FROM ONEMES.PPT_QC_CRBIS_DETAIL
    WHERE TANK_ID = '{tank}'
      AND DEFECT_TYPE = 4
      AND SAMPLE_TS >= TO_DATE('{start}', 'yyyy-mm-dd HH24:MI')
      AND SAMPLE_TS <= TO_DATE('{end}',   'yyyy-mm-dd HH24:MI')
    """


# ============================================================
# PPDA: defect details (per batch)
# ============================================================
def build_defect_query(batch_ids: list) -> str:
    """
    Heavy defect query for multiple BATCH_IDs (using IN clause).
    
    Note: Use chunks of <= 1000 to avoid Oracle ORA-01795.
    """
    in_clause = build_in_clause(batch_ids)
    return f"""
    SELECT DISTINCT
        U.BATCH_ID, U.SHEET_ID, U.LINE_ID,

        (case when (U.LINE_ID like '5%' or U.LINE_ID like '6%' or U.LINE_ID in ('401','301','303','304'))
              then NVL(NVL(DRS_LIS.X_POSITION, DRS_LIS1.X_POSITION), NVL(DRS_MRS.X_POS, ATS_MRS.X_POS))
              else NVL((case when ATS_MRS.X_POS is not NULL and ATS_MRS.X_POS > 0 then ATS_MRS.X_POS else ATS_LIS.X_POSITION end),
                       NVL(DRS_LIS.X_POSITION, DRS_LIS1.X_POSITION))
         end) as X_POSITION,

        (case when (U.LINE_ID like '5%' or U.LINE_ID like '6%' or U.LINE_ID in ('401','301','303','304'))
              then NVL(NVL(DRS_LIS.Y_POSITION, DRS_LIS1.Y_POSITION), NVL(DRS_MRS.Y_POS, ATS_MRS.Y_POS))
              else NVL((case when ATS_MRS.Y_POS is not NULL and ATS_MRS.Y_POS > 0 then ATS_MRS.Y_POS else ATS_LIS.Y_POSITION end),
                       NVL(DRS_LIS.Y_POSITION, DRS_LIS1.Y_POSITION))
         end) as Y_POSITION,

        (case when (U.LINE_ID like '5%' or U.LINE_ID like '6%' or U.LINE_ID in ('401','301','303','304'))
              then (case when NVL(DRS_LIS.LOSS_CODE, DRS_LIS1.LOSS_CODE) = '9600'
                         then DRS_LIS1.AUTO_LOSS_CODE
                         else NVL(DRS_LIS.LOSS_CODE, DRS_MRS.OPR_LOSS_CODE) end)
              else NVL(ATS_LIS.LOSS_CODE, DRS_LIS.LOSS_CODE)
         end) as LOSS_CODE,

        (case when (U.LINE_ID like '5%' or U.LINE_ID like '6%' or U.LINE_ID in ('401','301','303','304'))
              then NVL(NVL(DRS_LIS.DEFECT_TYPE, DRS_LIS1.DEFECT_TYPE), DRS_MRS.DEFECT_TYPE)
              else NVL(ATS_MRS.DEFECT_TYPE, NVL(DRS_LIS.DEFECT_TYPE, DRS_LIS1.DEFECT_TYPE))
         end) as LIS_DEFECT_TYPE,

        (case when (U.LINE_ID like '5%' or U.LINE_ID like '6%' or U.LINE_ID = '304')
              then DECODE(DRS_MRS.DEFECT_SIZE, '-1', DRS_MRS.MRS_DEFECT_SIZE, DRS_MRS.DEFECT_SIZE)
              else case when ATS_MRS.DEFECT_SIZE > 0 then ATS_MRS.DEFECT_SIZE
                        else ATS_MRS.MRS_DEFECT_SIZE end
         end) as MRS_SIZE,

        (case when (U.LINE_ID like '5%' or U.LINE_ID like '6%' or U.LINE_ID in ('401','301','303','304'))
              then NVL(DRS_LIS.DEFECT_SIZE, DRS_LIS1.DEFECT_SIZE)
              else NVL(NVL(ATS_LIS.DEFECT_SIZE, ATS_LIS1.DEFECT_SIZE), NVL(DRS_LIS.DEFECT_SIZE, DRS_LIS1.DEFECT_SIZE))
         end) as ISIS_SIZE

    FROM (
        SELECT LINE_ID, BATCH_ID, SHEET_ID
        FROM ONEMES.PDAS_LS_WARE
        WHERE BATCH_ID IN ({in_clause})
    ) U

    LEFT JOIN ONEMES.PDAS_LS_MRS_PARTICLE_V ATS_MRS
      ON U.BATCH_ID = ATS_MRS.WORK_ORD_NUM
     AND U.SHEET_ID = ATS_MRS.SHEET_NUM
     AND SUBSTR(ATS_MRS.OPR_LOSS_CODE, 2, 2) = '04'
     AND ATS_MRS.DEFECT_TYPE IN (0, 1, 3, 4, 5, 6, 7)

    LEFT JOIN ONEMES.PDAS_LS_ISIS_PARTICLE_V ATS_LIS
      ON U.BATCH_ID = ATS_LIS.WORK_ORD_NUM
     AND U.SHEET_ID = ATS_LIS.SHEET_NUM
     AND ATS_LIS.LOSS_CODE = 9999
     AND ATS_MRS.ISIS_DEFECT_ID = ATS_LIS.DEFECT_NUMBER

    LEFT JOIN ONEMES.PDAS_LS_ISIS_PARTICLE_V ATS_LIS1
      ON U.BATCH_ID = ATS_LIS1.WORK_ORD_NUM
     AND U.SHEET_ID = ATS_LIS1.SHEET_NUM
     AND ATS_LIS1.LOSS_CODE = 9999
     AND ATS_MRS.ISIS_DEFECT_ID IS NULL
     AND ABS(ATS_MRS.X_POS - ATS_LIS1.X_POSITION) < 5
     AND ABS(ATS_MRS.Y_POS - ATS_LIS1.Y_POSITION) < 5

    LEFT JOIN ONEMES.PDAS_LS_ISIS_PARTICLE_V DRS_LIS
      ON U.BATCH_ID = DRS_LIS.WORK_ORD_NUM
     AND U.SHEET_ID = DRS_LIS.SHEET_NUM
     AND SUBSTR(DRS_LIS.LOSS_CODE, 2, 2) = '04'
     AND DRS_LIS.DEFECT_TYPE IN (0, 1, 3, 4, 5, 6, 7)

    LEFT JOIN ONEMES.PDAS_LS_ISIS_PARTICLE_V DRS_LIS1
      ON U.BATCH_ID = DRS_LIS1.WORK_ORD_NUM
     AND U.SHEET_ID = DRS_LIS1.SHEET_NUM
     AND DRS_LIS1.LOSS_CODE = '9600'

    LEFT JOIN ONEMES.PDAS_LS_MRS_PARTICLE_V DRS_MRS
      ON U.BATCH_ID = DRS_MRS.WORK_ORD_NUM
     AND U.SHEET_ID = DRS_MRS.SHEET_NUM
     AND ((DRS_LIS.DEFECT_NUMBER IS NULL)
          OR (DRS_LIS.vendor_defect_id IS NULL AND DRS_LIS.DEFECT_NUMBER = DRS_MRS.DEFECT_NUM)
          OR (DRS_LIS.vendor_defect_id IS NOT NULL AND DRS_LIS.vendor_defect_id = DRS_MRS.vendor_defect_id))
     AND SUBSTR(DRS_MRS.OPR_LOSS_CODE, 2, 2) = '04'
     AND DRS_MRS.DEFECT_TYPE IN (0, 1, 3, 4, 5, 6, 7)
    """


# ============================================================
# Cube: defect-loss MDX
# ============================================================
def build_cube_query(crate_ids: list) -> str:
    crate_set = ",\n            ".join(
        f"[Finishing Source Tank].[Mother Crate ID].&[{cid}]"
        for cid in crate_ids
    )
    return f"""
    SELECT
        {{[Measures].[F_Defect Loss%]}} ON COLUMNS,
        NON EMPTY
        (
            [Finishing Source Tank].[Mother Crate ID].[Mother Crate ID].MEMBERS
            *
            [FG Product].[FG_Gen].[FG_Gen].MEMBERS
            *
            [Defect Tracking].[Defect ID].[Defect ID].MEMBERS
        ) ON ROWS
    FROM (
        SELECT
            {{ {crate_set} }} ON COLUMNS
        FROM [PPD_Actual]
    )
    WHERE (
        [Defect Tracking].[Defect Group].&[F_Material Loss]
    )
    """