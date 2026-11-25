import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def create_launch_banner(
    screenshot_path: str,
    output_path: str,
    width: int = 1200,
    height: int = 675
):
    # Base background: Deep sleek dark charcoal/navy with subtle gradient
    img = Image.new("RGBA", (width, height), (11, 15, 23, 255))
    draw = ImageDraw.Draw(img)

    # 1. Subtle glowing mesh/gradients in background
    # Top-left subtle emerald glow
    glow1 = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    g1_draw = ImageDraw.Draw(glow1)
    g1_draw.ellipse([(-100, -100), (450, 450)], fill=(16, 185, 129, 35))
    # Bottom-right cyan/purple glow
    g1_draw.ellipse([(width - 450, height - 350), (width + 100, height + 100)], fill=(14, 165, 233, 40))
    glow1 = glow1.filter(ImageFilter.GaussianBlur(80))
    img = Image.alpha_composite(img, glow1)
    draw = ImageDraw.Draw(img)

    # Fonts
    font_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font_reg = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
    
    title_font = ImageFont.truetype(font_bold, 42)
    tag_font = ImageFont.truetype(font_bold, 13)
    subtitle_font = ImageFont.truetype(font_reg, 18)
    card_title_font = ImageFont.truetype(font_bold, 15)
    card_desc_font = ImageFont.truetype(font_reg, 12)
    footer_font = ImageFont.truetype(font_reg, 13)
    pill_font = ImageFont.truetype(font_bold, 12)

    # 2. Top-Left Badge: "PRODUCTION LAUNCH"
    badge_x, badge_y = 50, 40
    badge_w, badge_h = 165, 28
    draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], radius=14, fill=(16, 185, 129, 30), outline=(16, 185, 129, 180), width=1)
    draw.ellipse([badge_x + 12, badge_y + 10, badge_x + 20, badge_y + 18], fill=(16, 185, 129, 255))
    draw.text((badge_x + 28, badge_y + 6), "PRODUCTION LAUNCH", font=tag_font, fill=(52, 211, 153, 255))

    # 3. Main Brand Title
    draw.text((50, 80), "FolioGuard", font=title_font, fill=(255, 255, 255, 255))

    # Accent color for "Guard"
    # Measure "Folio"
    folio_bbox = draw.textbbox((50, 80), "Folio", font=title_font)
    draw.text((folio_bbox[2], 80), "Guard", font=title_font, fill=(52, 211, 153, 255))

    # 4. Subtitle
    draw.text((50, 136), "Institutional-Grade AI Portfolio Assistant for Indian Investors", font=subtitle_font, fill=(156, 163, 175, 255))

    # 5. Left Feature Highlight Cards
    features = [
        ("🤖 3-Stage Gemini Advisory", "Pre-flight guards -> NSE screening -> Budget-capped orders", (14, 165, 233)),
        ("📊 Deterministic Math Engine", "Newton-Raphson XIRR, Beta vs NIFTY 50, Sharpe & Sortino", (52, 211, 153)),
        ("📉 Tax-Loss Harvesting", "Budget 2024 rules: STCG 20%, LTCG 12.5%, ₹1.25L exemption", (245, 158, 11)),
        ("⚡ Zerodha Kite Ingestion", "Zero credential retention + Fernet AES-256 encryption", (168, 85, 247))
    ]

    card_y = 185
    card_w = 480
    card_h = 68
    card_spacing = 15

    for title, desc, accent_color in features:
        # Glass card background
        card_rect = [50, card_y, 50 + card_w, card_y + card_h]
        draw.rounded_rectangle(card_rect, radius=10, fill=(17, 24, 39, 210), outline=(55, 65, 81, 180), width=1)
        # Left accent vertical indicator
        draw.rounded_rectangle([50, card_y + 12, 54, card_y + card_h - 12], radius=2, fill=accent_color)
        
        # Text
        draw.text((68, card_y + 12), title, font=card_title_font, fill=(243, 244, 246, 255))
        draw.text((68, card_y + 38), desc, font=card_desc_font, fill=(156, 163, 175, 255))
        
        card_y += card_h + card_spacing

    # 6. Right Side: Screenshot Mockup
    if os.path.exists(screenshot_path):
        screenshot = Image.open(screenshot_path).convert("RGBA")
        
        # Frame dimensions
        frame_x, frame_y = 560, 80
        frame_w, frame_h = 590, 450
        
        # Resize screenshot to fit inside frame
        ss_resized = screenshot.resize((frame_w - 4, frame_h - 32), Image.Resampling.LANCZOS)
        
        # Mockup window container
        mockup = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
        m_draw = ImageDraw.Draw(mockup)
        
        # Window frame with dark sleek border
        m_draw.rounded_rectangle([0, 0, frame_w, frame_h], radius=12, fill=(24, 31, 46, 255), outline=(75, 85, 99, 200), width=1)
        
        # Browser window dots
        m_draw.ellipse([14, 12, 22, 20], fill=(239, 68, 68, 255))
        m_draw.ellipse([28, 12, 36, 20], fill=(245, 158, 11, 255))
        m_draw.ellipse([42, 12, 50, 20], fill=(16, 185, 129, 255))
        
        # URL bar pill
        m_draw.rounded_rectangle([70, 7, frame_w - 70, 25], radius=6, fill=(15, 23, 42, 255))
        m_draw.text((85, 9), "🔒 portfolio-assistant-rouge.vercel.app", font=ImageFont.truetype(font_reg, 10), fill=(156, 163, 175, 255))
        
        # Paste screenshot into mockup below title bar
        mockup.paste(ss_resized, (2, 30))
        
        # Add shadow behind mockup
        shadow = Image.new("RGBA", (frame_w + 40, frame_h + 40), (0, 0, 0, 0))
        s_draw = ImageDraw.Draw(shadow)
        s_draw.rounded_rectangle([15, 15, frame_w + 25, frame_h + 25], radius=16, fill=(0, 0, 0, 160))
        shadow = shadow.filter(ImageFilter.GaussianBlur(18))
        
        img.paste(shadow, (frame_x - 20, frame_y - 20), shadow)
        img.paste(mockup, (frame_x, frame_y), mockup)
        draw = ImageDraw.Draw(img)

    # 7. Bottom Tech Stack Pills & Footer
    pills = ["Next.js 14", "FastAPI", "GCP Cloud Run", "Supabase PostgreSQL", "Upstash Redis", "Google Gemini"]
    pill_x = 50
    pill_y = 540
    for p in pills:
        pw = int(draw.textlength(p, font=pill_font)) + 20
        draw.rounded_rectangle([pill_x, pill_y, pill_x + pw, pill_y + 24], radius=12, fill=(31, 41, 55, 180), outline=(75, 85, 99, 150), width=1)
        draw.text((pill_x + 10, pill_y + 5), p, font=pill_font, fill=(209, 213, 219, 255))
        pill_x += pw + 10

    # 8. Bottom Footer separator and attribution
    draw.line([(50, 595), (width - 50, 595)], fill=(55, 65, 81, 150), width=1)
    draw.text((50, 615), "Crafted by Benoi Rajan · Full-Stack & AI Systems", font=footer_font, fill=(156, 163, 175, 255))
    
    # Right-aligned CTA
    cta_text = "Live Demo: portfolio-assistant-rouge.vercel.app"
    cta_w = int(draw.textlength(cta_text, font=footer_font))
    draw.text((width - 50 - cta_w, 615), cta_text, font=footer_font, fill=(52, 211, 153, 255))

    # Convert to RGB and save
    final_img = img.convert("RGB")
    final_img.save(output_path, "PNG", quality=95)
    print(f"Banner generated successfully at {output_path}")

if __name__ == "__main__":
    screenshot = ".reports/e2e_screenshots/01_landing_page.png"
    output = "docs/plans/campaigns/assets/folioguard_launch_infographic.png"
    create_launch_banner(screenshot, output)
