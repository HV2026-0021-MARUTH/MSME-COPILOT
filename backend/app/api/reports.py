from app.api.deps import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.report_service import (
    collect_report_data, generate_pdf_report, generate_xlsx_report, generate_png_report
)

router = APIRouter(prefix="/api/reports", tags=["Business Reports"], dependencies=[Depends(get_current_user)])

@router.get("/business/pdf")
@router.get("/pdf")
def download_pdf_report(
    period: str = Query("7d", description="Report period: today, 7d, 30d"),
    shop_id: str = "shop_001",
    db: Session = Depends(get_db)
):
    """
    Download Business Report in PDF format.
    CRITICAL SAFETY GUARANTEE: READ-ONLY. Zero database mutations.
    """
    data = collect_report_data(db, shop_id, period)
    pdf_bytes = generate_pdf_report(data)
    filename = f"maruthi_report_{period}_{data['metadata']['period_end']}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/business/xlsx")
@router.get("/xlsx")
def download_xlsx_report(
    period: str = Query("7d", description="Report period: today, 7d, 30d"),
    shop_id: str = "shop_001",
    db: Session = Depends(get_db)
):
    """
    Download Business Report in Excel XLSX format (7 distinct sheets).
    CRITICAL SAFETY GUARANTEE: READ-ONLY. Zero database mutations.
    """
    data = collect_report_data(db, shop_id, period)
    xlsx_bytes = generate_xlsx_report(data)
    filename = f"maruthi_report_{period}_{data['metadata']['period_end']}.xlsx"

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/business/png")
@router.get("/png")
def download_png_report(
    period: str = Query("7d", description="Report period: today, 7d, 30d"),
    shop_id: str = "shop_001",
    db: Session = Depends(get_db)
):
    """
    Download Executive Summary Snapshot Card in PNG format (WhatsApp / mobile shareable).
    CRITICAL SAFETY GUARANTEE: READ-ONLY. Zero database mutations.
    """
    data = collect_report_data(db, shop_id, period)
    png_bytes = generate_png_report(data)
    filename = f"maruthi_snapshot_{period}_{data['metadata']['period_end']}.png"

    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )
