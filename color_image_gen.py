import os
import re

from PIL import Image, ImageDraw, ImageFont

from color_name_map import COLOR_NAME_MAP


def generate_color_map(guild_id: int, images_dir: str = "images") -> str:
	"""Generate and save a labeled Rocket League color palette image for a guild."""
	families: dict[str, list[tuple[int, str, str]]] = {}
	for name, hex_code in COLOR_NAME_MAP.items():
		match = re.fullmatch(r"(.+?)(\d+)", name)
		if match is None:
			continue
		family, tone = match.group(1), int(match.group(2))
		families.setdefault(family, []).append((tone, name, hex_code))

	for colors in families.values():
		colors.sort(key=lambda color: color[0])

	margin = 24
	column_width = 112
	header_height = 48
	row_height = 76
	swatch_width = 88
	swatch_height = 38
	rows = max((len(colors) for colors in families.values()), default=0)
	image_width = margin * 2 + column_width * len(families)
	image_height = margin * 2 + header_height + row_height * rows

	image = Image.new("RGB", (image_width, image_height), "#20252b")
	draw = ImageDraw.Draw(image)
	title_font = ImageFont.load_default(size=20)
	label_font = ImageFont.load_default(size=14)

	for column, (family, colors) in enumerate(families.items()):
		cell_x = margin + column * column_width
		draw.text((cell_x, margin), family.title(), fill="#f3f5f7", font=title_font)

		for row, (_, name, hex_code) in enumerate(colors):
			cell_y = margin + header_height + row * row_height
			swatch_x = cell_x
			swatch_y = cell_y
			draw.rounded_rectangle(
				(swatch_x, swatch_y, swatch_x + swatch_width, swatch_y + swatch_height),
				radius=4,
				fill=f"#{hex_code}",
				outline="#ffffff",
				width=1,
			)
			draw.text(
				(swatch_x, swatch_y + swatch_height + 4),
				name,
				fill="#f3f5f7",
				font=label_font,
			)

	output_dir = os.path.join(images_dir, f"guild_{guild_id}", "color_map")
	os.makedirs(output_dir, exist_ok=True)
	output_path = os.path.join(output_dir, "color_map.png")
	image.save(output_path)
	return output_path
