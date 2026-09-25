from PIL import Image, ImageDraw, ImageFont
import os
import requests
from typing import Optional, List
from bracketool.domain import Competitor, Clash
from diagrams import Diagram, Node, Edge, Cluster
from diagrams.custom import Custom
import tempfile

FONT_CACHE_DIR = os.path.expanduser("~/.cache/imagegen/fonts")

def get_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    """
    Load a TTF from the local ./fonts directory by name + size.
    Expects a mapping from font name to .ttf filename in ./fonts/.
    """
    name_l = name.lower()
    match name_l:
        case "roboto":
            filename = "Roboto_Condensed-Regular.ttf"
        case "roboto_italic":
            filename = "Roboto_Condensed-Italic.ttf"
        case _:
            raise ValueError(f"No local font configured for '{name}'")

    path = os.path.join("fonts", filename)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Font file not found: {path}")

    return ImageFont.truetype(path, size)



class GeneratedImage:
    """
    Wrapper for a PIL Image to enable chained save operations using a base directory.
    """
    def __init__(self, image: Image.Image, base_dir: str):
        self._image = image
        self._base_dir = base_dir
        self._full_saved_path = None

    def save(self, relative_path: str):
        """
        Save the image under the base directory, ensuring subdirectories exist.
        Returns self for chaining.

        Example:
            gen = ImageGen("images")
            gen.create_clash_box("A","B").save("icons/round1_clash0.png")
        """
        full_path = os.path.join(self._base_dir, relative_path)
        self._full_saved_path = full_path
        folder = os.path.dirname(full_path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        self._image.save(full_path)
        return self
    
    def get_save_path(self):
        """
        Returns the full path of the saved image.
        """
        return self._full_saved_path
    
    def set_base_dir(self, new_base_dir: str):
        """
        Update the base directory for saving images.
        """
        self._base_dir = new_base_dir
        return self
    
    def add_text_to_img(
        self,
        text: str,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        font_name: str = "roboto",
        font_size: int = 24,
        text_color: str = "black",
        background_color: str = None,
        align: str = "center"
    ):
        """
        Add text to the image within the specified rectangle.
        The text will be centered within the rectangle and scaled down if necessary to fit.
        
        Args:
            text: The text to add
            x1, y1: Top-left corner of the rectangle
            x2, y2: Bottom-right corner of the rectangle
            font_name: Name of the font to use (must be available via get_font)
            font_size: Starting font size (will be reduced if text doesn't fit)
            text_color: Color of the text
            background_color: Optional background color for the text area
            align: Text alignment - "center" (default), "left", or "right"
            
        Returns:
            self for chaining
        """
        draw = ImageDraw.Draw(self._image)
        
        # Calculate rectangle dimensions
        rect_width = x2 - x1
        rect_height = y2 - y1
        
        # Draw background if specified
        if background_color:
            draw.rectangle([(x1, y1), (x2, y2)], fill=background_color)
        
        # Helper to measure text
        def measure(text_to_measure: str, font_obj) -> tuple[int, int]:
            bbox = draw.textbbox((0, 0), text_to_measure, font=font_obj)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        
        # Find a font size that fits the rectangle
        current_font_size = font_size
        current_font = get_font(font_name, current_font_size)
        text_width, text_height = measure(text, current_font)
        
        # Reduce font size until text fits within rectangle
        while (text_width > rect_width or text_height > rect_height) and current_font_size > 8:
            current_font_size -= 1
            current_font = get_font(font_name, current_font_size)
            text_width, text_height = measure(text, current_font)
        
        # Calculate position based on alignment
        if align == "center":
            text_x = x1 + (rect_width - text_width) // 2
            text_y = y1 + (rect_height - text_height) // 2
        elif align == "left":
            text_x = x1 + 5  # Small padding from left
            text_y = y1 + (rect_height - text_height) // 2
        elif align == "right":
            text_x = x2 - text_width - 5  # Small padding from right
            text_y = y1 + (rect_height - text_height) // 2
        else:
            # Default to center if invalid alignment
            text_x = x1 + (rect_width - text_width) // 2
            text_y = y1 + (rect_height - text_height) // 2
        
        # Draw the text
        draw.text((text_x, text_y), text, fill=text_color, font=current_font)
        
        return self

class ImageGen:
    """
    Utility for generating bracket images. Supports method chaining.

    Example:
        image_gen = ImageGen(output_dir="images")
        image_gen.create_clash_box("Team A","Team B").save("icons/r1_c0.png")
    """
    def __init__(self, output_dir: str = "images"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        os.environ["GDFONTPATH"] = os.path.abspath("fonts")

    def create_clash_box(
        self,
        top_text: str,
        bottom_text: str,
        width: int = 200,
        height: int = 100,
        background_color: str = "white",
        font_color: str = "black",
        border_color: str = "black",
        border_width: int = 2,
        line_width: int = 1,
        font_size: int | None = None,
        font: Optional[ImageFont.ImageFont] = None,
        top_box_color: str | None = None,
        top_text_color: str | None = None,
        bottom_box_color: str | None = None,
        bottom_text_color: str | None = None,
        top_box_score: str | None = None,
        bottom_box_score: str | None = None,
    ) -> GeneratedImage:
        """
        Create a clash box image and return a GeneratedImage for chaining.
        You can now specify separate colors for each half of the box,
        plus optional score text on the right side.
        """
        # default the half-box colors and text colors
        top_box_color     = top_box_color     or background_color
        bottom_box_color  = bottom_box_color  or background_color
        top_text_color    = top_text_color    or font_color
        bottom_text_color = bottom_text_color or font_color

        img = Image.new("RGB", (width, height), background_color)
        draw = ImageDraw.Draw(img)
        mid_y = height // 2

        # fill halves
        draw.rectangle([(0, 0), (width - 1, mid_y - 1)], fill=top_box_color)
        draw.rectangle([(0, mid_y), (width - 1, height - 1)], fill=bottom_box_color)

        # dividing line & border
        draw.line([(0, mid_y), (width, mid_y)], fill=border_color, width=line_width)
        draw.rectangle([(0, 0), (width - 1, height - 1)], outline=border_color, width=border_width)

        # Set default font size if not provided
        if font_size is None:
            font_size = 24
        
        # Helper to measure text
        def measure(text: str, font_obj) -> tuple[int, int]:
            bbox = draw.textbbox((0, 0), text, font=font_obj)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        
        # Helper to get appropriate font size for text to fit width
        def get_fitting_font(text: str, max_width: int, start_size: int, font_name: str = "roboto") -> ImageFont.FreeTypeFont:
            test_size = start_size
            test_font = get_font(font_name, test_size)
            text_width, _ = measure(text, test_font)
            
            # Reserve some space for padding and score if needed
            effective_width = max_width - 20  # 10px padding on each side
            # if top_box_score is not None or bottom_box_score is not None:
            #     effective_width -= 50  # Reserve space for score
            
            # Reduce font size until text fits
            while text_width > effective_width and test_size > 8:  # 8 is minimum readable size
                test_size -= 1
                test_font = get_font(font_name, test_size)
                text_width, _ = measure(text, test_font)
            
            return test_font
        
        # Get appropriate fonts for top and bottom text
        max_text_width = width - 20  # 10px padding on each side
        
        # Calculate the longest text between top and bottom
        top_font = get_fitting_font(top_text, max_text_width, font_size)
        bottom_font = get_fitting_font(bottom_text, max_text_width, font_size)
        
        # Draw centered competitor names
        tw, th = measure(top_text, top_font)
        draw.text(
            ((width - tw) / 2, (mid_y - th) / 2),
            top_text,
            fill=top_text_color,
            font=top_font,
        )

        bw, bh = measure(bottom_text, bottom_font)
        draw.text(
            ((width - bw) / 2, mid_y + (mid_y - bh) / 2),
            bottom_text,
            fill=bottom_text_color,
            font=bottom_font,
        )

        # Use smaller font for scores
        score_font_size = int(font_size * 0.75)
        score_font = get_font("roboto_italic", score_font_size)
        
        # Draw optional scores on right side with padding
        padding = 5
        if top_box_score is not None:
            sw, sh = measure(top_box_score, score_font)
            x = width - sw - padding
            y = (mid_y - sh) / 2
            draw.text((x, y), top_box_score, fill=top_text_color, font=score_font)

        if bottom_box_score is not None:
            sw, sh = measure(bottom_box_score, score_font)
            x = width - sw - padding
            y = mid_y + (mid_y - sh) / 2
            draw.text((x, y), bottom_box_score, fill=bottom_text_color, font=score_font)

        return GeneratedImage(img, self.output_dir)



    def create_bracket(
        self,
        rounds: List[List[Clash]],
        current_round: int = 1
    ) -> GeneratedImage:
        """
        rounds: list of rounds; each round is a list of Clash objects.
        current_round: 1-based index of the active round to highlight.
        """
        # prepare temp output
        tmp_dir  = tempfile.mkdtemp()
        dot_path = os.path.join(tmp_dir, "bracket")
        graph_attr = {
            "rankdir": "LR",
            "nodesep":  "0.5",
            "ranksep":  "1.0",
            "splines":  "ortho",
            "fontname": "Oswald-Medium",
            "fontsize:": "40"
        }

        nodes_by_round: List[List[Node]] = []

        with Diagram(
            "Team Name Bracket 2.0",
            filename=dot_path,
            show=False,
            direction="LR",
            graph_attr=graph_attr
        ):

            # 1) create one cluster per round, highlighting the current one
            for r_idx, clashes in enumerate(rounds):
                round_nodes: List[Node] = []
                # highlight settings for active round
                if (r_idx + 1) == current_round:
                    cluster_attrs = {
                        "style": "filled",
                        "fillcolor": "lightblue",
                        "color": "blue"
                    }
                else:
                    cluster_attrs = {
                        "style": "rounded",
                        "color": "gray"
                    }

                total_players_in_round = 2 ** (len(rounds) - r_idx)
                round_name = f"Top {total_players_in_round}"
                # on last round
                if(r_idx + 1) == len(rounds):
                    round_name = "Grand Finals"
                elif(r_idx + 1) == len(rounds) - 1:
                    round_name = "Semi Finals"
                elif(r_idx + 1) == len(rounds) - 2:
                    round_name = "Quarter Finals"

                with Cluster(
                    round_name,
                    direction="TB",
                    graph_attr=cluster_attrs
                ):
                    win_score_index = []
                    lose_score_index = []
                    for c_idx, clash in enumerate(clashes):
                        win_score_index.append(c_idx)
                        lose_score_index.append(c_idx + len(win_score_index))

                        # get competitor names (or "TBA")
                        comp_a = (
                            clash.competitor_a.name
                            if clash.competitor_a and getattr(clash.competitor_a, "name", "")
                            else "TBA"
                        )
                        comp_b = (
                            clash.competitor_b.name
                            if clash.competitor_b and getattr(clash.competitor_b, "name", "")
                            else "TBA"
                        )

                        # detect winner if present
                        winner_name = getattr(clash, "winner", None)
                        win_score = getattr(clash, "win_score", None)
                        lost_score = getattr(clash, "lost_score", None)

                        # default colors
                        default_box_color    = "white"
                        default_text_color   = "black"
                        winner_box_color     = "#a0f2c9"
                        winner_text_color    = "#111a15"
                        bottom_box_score     = None
                        top_box_score        = None

                        # decide top/bottom styling
                        if winner_name == comp_a:
                            top_box_color    = winner_box_color
                            top_text_color   = winner_text_color
                            top_box_score = win_score
                            bottom_box_score = lost_score
                        else:
                            top_box_color    = default_box_color
                            top_text_color   = default_text_color
                            top_box_score = lost_score
                            bottom_box_score = win_score

                        if winner_name == comp_b:
                            bottom_box_color  = winner_box_color
                            bottom_text_color = winner_text_color
                        else:
                            bottom_box_color  = default_box_color
                            bottom_text_color = default_text_color

                        # generate and save the clash-box image
                        icon_rel = f"icons/match_{r_idx+1}_{c_idx+1}.png"
                        self.create_clash_box(
                            top_text=comp_a,
                            bottom_text=comp_b,
                            width=200,
                            height=100,
                            font_size=24,
                            top_box_color=top_box_color,
                            top_text_color=top_text_color,
                            bottom_box_color=bottom_box_color,
                            bottom_text_color=bottom_text_color,
                            bottom_box_score=None if bottom_box_score is None else str(bottom_box_score),
                            top_box_score=None if top_box_score is None else str(top_box_score)
                        ).save(icon_rel)

                        # load it into a Custom node
                        icon_abspath = os.path.abspath(
                            os.path.join(self.output_dir, icon_rel)
                        )
                        node = Custom(
                            "",
                            icon_abspath,
                            shape="none",
                            margin="0",
                            fixedsize="true"
                        )
                        round_nodes.append(node)


                nodes_by_round.append(round_nodes)

            # 2) connect winners from each pair in round r to the node in round r+1
            for r_idx in range(len(nodes_by_round) - 1):
                prev_nodes = nodes_by_round[r_idx]
                next_nodes = nodes_by_round[r_idx + 1]
                for out_idx, target in enumerate(next_nodes):
                    left  = prev_nodes[out_idx * 2]
                    right = prev_nodes[out_idx * 2 + 1]
                    left  >> Edge() >> target
                    right >> Edge() >> target

        # 3) load & wrap
        img = Image.open(dot_path + ".png")
        w, h = img.size
        px = int(w * 0.05)   # 5% horizontally1
        py = int(h * 0.05)   # 5% vertically
        img = img.crop((px, py, w - px, h - py))
        return GeneratedImage(img, self.output_dir)
    

    def create_text_image(
        self,
        width: int,
        height: int,
        background_color: str = "white"
    ) -> GeneratedImage:
        """
        Create a blank image with the specified dimensions and background color.
        Returns a GeneratedImage for chaining text additions and saving.
        
        Example:
            image_gen.create_text_image(800, 600).add_text_to_img("Hello", 10, 10, 200, 50).save("text_image.png")
        """
        img = Image.new("RGB", (width, height), background_color)
        return GeneratedImage(img, self.output_dir)

    def load_image(
        self,
        image_path: str
    ) -> GeneratedImage:
        """
        Load an existing image from the specified path.
        Returns a GeneratedImage for chaining text additions and saving.
        
        Example:
            image_gen.load_image("background.png").add_text_to_img("Hello", 10, 10, 200, 50).save("annotated.png")
        """
        # Check if path is absolute or relative to output directory
        if os.path.isabs(image_path):
            full_path = image_path
        else:
            full_path = os.path.join(self.output_dir, image_path)
        
        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"Image file not found: {full_path}")
        
        img = Image.open(full_path)
        # Convert to RGB if needed (in case of RGBA or other formats)
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        return GeneratedImage(img, self.output_dir)

