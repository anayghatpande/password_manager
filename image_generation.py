from PIL import Image, ImageDraw, ImageFont

def create_placeholder_icon(filename, color):
    size = (60, 60)  # Set icon size
    img = Image.new("RGB", size, color)
    draw = ImageDraw.Draw(img)

    # Try to load a font that supports Unicode characters (like emojis)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 20)  # or use another font path
    except IOError:
        font = ImageFont.load_default()  # Fallback to default font if custom font fails

    # Draw the lock emoji (🔒)
    draw.text((15, 15), "🔒", font=font, fill="white")
    
    # Save the image
    img.save(filename)

# Create the icons
create_placeholder_icon("locked.png", "gray")  # Locked icon
create_placeholder_icon("unlocked.png", "green")  # Unlocked icon
