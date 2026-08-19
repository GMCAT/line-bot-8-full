"""ระบบราคาหุ้น แยกจากระบบข่าว"""


def get_stock_price(ticker: str) -> str:
    """ดึงราคาหุ้นล่าสุดด้วย yfinance เช่น AAPL, PTT.BK, DELTA.BK"""
    try:
        import yfinance as yf

        ticker_data = yf.Ticker(ticker)
        info = ticker_data.fast_info
        price = info.get("last_price")
        previous_close = info.get("previous_close")
        if price is None:
            return f'ไม่พบข้อมูลราคาหุ้นของ "{ticker}" ครับ ลองตรวจสอบสัญลักษณ์หุ้นอีกครั้ง'
        change = price - previous_close if previous_close else 0
        percent = (change / previous_close * 100) if previous_close else 0
        arrow = "🔺" if change > 0 else ("🔻" if change < 0 else "➖")
        return f"📈 {ticker}: {price:,.2f} {arrow} {change:+.2f} ({percent:+.2f}%)"
    except Exception as exc:
        return f'ดึงราคาหุ้น "{ticker}" ไม่สำเร็จ: {exc}'
