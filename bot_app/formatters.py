import html
import re
from datetime import datetime

def escape_ai_text(text):
    """Escape special characters for Telegram HTML but preserve Markdown bold."""
    if not text:
        return ""
    escaped = html.escape(text)
    escaped = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', escaped)
    return escaped

def format_scorecard_message(target_symbol, scorecard, strategy_result):
    """Format scorecard to a Telegram HTML message — đầy đủ theo chi_so.md."""
    price = scorecard.get('current_price', 0)
    change_1d = scorecard.get('1D_pct', 0)
    change_1m = scorecard.get('1M_pct', 0)
    change_1y = scorecard.get('1Y_pct', 0)
    consecutive = scorecard.get('consecutive_up', 0)
    rs_avg = scorecard.get('rs_avg', 0)
    vol_sma10 = scorecard.get('vol_vs_sma10_pct', 0)
    vol_sma20 = scorecard.get('vol_vs_sma20_pct', 0)
    active_buy = scorecard.get('active_buy_pct', 0)
    foreign_net = scorecard.get('foreign_net_vol_20d', 0)
    price_ma10 = scorecard.get('price_vs_ma10_pct', 0)
    price_ma20 = scorecard.get('price_vs_ma20_pct', 0)
    price_ma50 = scorecard.get('price_vs_ma50_pct', 0)
    beta = scorecard.get('beta', 'N/A')
    rsi = scorecard.get('rsi_14', 0)
    rsi_status = scorecard.get('rsi_status', '')
    macd = scorecard.get('macd_hist', 0)
    macd_status = scorecard.get('macd_status', '')

    sec_pe = scorecard.get('Security_PE')
    ind_pe = scorecard.get('Industry_PE')
    sec_roe = scorecard.get('Security_ROE')
    ind_roe = scorecard.get('Industry_ROE')
    
    buy_active_ratio = scorecard.get('buy_active_ratio')
    
    prop_val_1d = scorecard.get('proprietary_val_1d')
    prop_val_10d = scorecard.get('proprietary_val_10d')
    
    rrg_short_rs = scorecard.get('rrg_short_rs')
    rrg_short_rm = scorecard.get('rrg_short_rm')
    rrg_mid_rs = scorecard.get('rrg_mid_rs')
    rrg_mid_rm = scorecard.get('rrg_mid_rm')
    rrg_drawdown_status = scorecard.get('rrg_drawdown_status')
    rrg_drawdown_value = scorecard.get('rrg_drawdown_value')

    change_icon = "🟢" if change_1d > 0 else "🔴" if change_1d < 0 else "🟡"
    rs_icon = "💪" if rs_avg > 0 else "📉"
    rsi_icon = "🔴" if rsi >= 70 else "🟢" if rsi <= 30 else "🟡"

    msg = f"<b>📊 BÁO CÁO KỸ THUẬT: {target_symbol}</b>\n"
    msg += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    msg += f"<b>1. Giá & Biến động:</b>\n"
    msg += f"• Giá: <code>{price:,.0f}</code> ({change_icon} {change_1d:+.2f}%)\n"
    msg += f"• 1M: <code>{change_1m:+.2f}%</code> | 1Y: <code>{change_1y:+.2f}%</code>\n"
    msg += f"• Phiên tăng liên tiếp: <code>{consecutive}</code>\n"
    msg += f"• Beta: <code>{beta}</code>\n"
    if sec_pe is not None and ind_pe is not None:
        msg += f"• P/E: <code>{sec_pe:.1f}</code> (Ngành: <code>{ind_pe:.1f}</code>)\n"
    if sec_roe is not None and ind_roe is not None:
        msg += f"• ROE: <code>{sec_roe:.1f}%</code> (Ngành: <code>{ind_roe:.1f}%</code>)\n"
    msg += "\n"

    msg += f"<b>2. Khối lượng & Dòng tiền:</b>\n"
    msg += f"• KL/SMA10: <code>{vol_sma10:.0f}%</code> | KL/SMA20: <code>{vol_sma20:.0f}%</code>\n"
    msg += f"• Mua chủ động: <code>{active_buy:.1f}%</code>\n"
    if buy_active_ratio is not None:
        msg += f"• Lực mua chủ động (Order Flow): <code>{buy_active_ratio:.1f}%</code>\n"
    msg += f"• KN ròng 20 phiên: <code>{foreign_net:,.0f}</code>\n"
    if prop_val_1d is not None and prop_val_10d is not None:
        msg += f"• Tự doanh ròng: 1D: <code>{prop_val_1d:+.1f}B</code> | 10D: <code>{prop_val_10d:+.1f}B</code>\n"
    msg += "\n"

    msg += f"<b>3. Kỹ thuật & RRG:</b>\n"
    msg += f"• {rsi_icon} RSI(14): <code>{rsi:.1f}</code> ({rsi_status})\n"
    msg += f"• MACD Hist: <code>{macd:+.4f}</code> ({macd_status})\n"
    msg += f"• Giá/MA10: <code>{price_ma10:+.2f}%</code>\n"
    msg += f"• Giá/MA20: <code>{price_ma20:+.2f}%</code>\n"
    msg += f"• Giá/MA50: <code>{price_ma50:+.2f}%</code>\n"
    msg += f"• {rs_icon} RS TB (vs Custom VNI): <code>{rs_avg:+.2f}</code>\n"
    if rrg_mid_rs is not None and rrg_mid_rm is not None:
        msg += f"• RRG Mid-term: RS: <code>{rrg_mid_rs:.1f}</code> | RM: <code>{rrg_mid_rm:.1f}</code>\n"
    if rrg_short_rs is not None and rrg_short_rm is not None:
        msg += f"• RRG Short-term: RS: <code>{rrg_short_rs:.1f}</code> | RM: <code>{rrg_short_rm:.1f}</code>\n"
    if rrg_drawdown_status is not None:
        msg += f"• Trạng thái Drawdown: <code>{rrg_drawdown_status} ({rrg_drawdown_value:+.2f}%)</code>\n"
    msg += "\n"

    signal = strategy_result['signal']
    signal_icon = "🔥" if signal == "Phá nền" else "🚀" if signal == "Từ đáy bật lên" else "⏸"
    msg += f"<b>4. Tín hiệu: {signal_icon} {signal}</b>\n"
    if strategy_result['details']:
        for detail in strategy_result['details']:
            msg += f"  ✓ <i>{detail}</i>\n"

    return msg

def format_overall_message(overall_summary):
    """Format overall summary to a Telegram HTML message."""
    escaped_summary = escape_ai_text(overall_summary)
    msg = "<b>🌐 BÁO CÁO TỔNG QUAN THỊ TRƯỜNG</b>\n"
    msg += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    msg += f"<b>🤖 ĐÁNH GIÁ & KHUYẾN NGHỊ TỔNG HỢP:</b>\n"
    msg += f"{escaped_summary}\n"
    return msg
