import os
from dataclasses import dataclass
from bracketool.single_elimination import SingleEliminationGen
from bracketool.domain import Competitor, Clash as BOClash
from typing import Optional, List
from image_gen import ImageGen
from PIL import ImageFont

@dataclass
class ClashInfo:
    """
    A simple container for a single match-up (clash).
    """
    round: int
    index: int
    team1: str
    team2: str

class Bracket:
    """
    Manages a single-elimination bracket using bracketool and diagrams.
    """
    def __init__(self):
        self.rounds: int = 0
        self._participants: list[tuple[str, int]] = []
        self._gen: SingleEliminationGen | None = None
        self._bracket = None

    def add_name(self, name: str, rating: int) -> None:
        """
        Add a new participant by name and rating. Seeds are adjusted
        by rating descending. Cannot add once rounds > 0.
        """
        if self.rounds != 0:
            raise RuntimeError("Cannot add names after bracket has started")
        self._participants.append((name, rating))

    def finalize(self) -> None:
        """
        Lock in participants and seed the bracket. Moves from setup
        (rounds=0) to first round (rounds=1).
        """
        if self.rounds != 0:
            raise RuntimeError("Bracket already finalized")
        if len(self._participants) < 2:
            raise RuntimeError("Need at least two participants to finalize")

        self.rounds = 1
        # sort by rating (highest first) for seeding
        seeds = sorted(self._participants, key=lambda x: x[1], reverse=True)
        # build Competitor objects (no team grouping)
        competitors = [Competitor(name, "", rating) for name, rating in seeds]

        # initialize and generate the bracket structure
        se = SingleEliminationGen(
            use_three_way_final=False,
            third_place_clash=False,
            use_rating=True,
            use_teams=False,
            random_seed=None
        )
        self._gen = se
        self._bracket = se.generate(competitors)

    def get_next_clash(self) -> ClashInfo:
        if self.rounds == 0 or self._bracket is None:
            raise RuntimeError("Bracket not started")

        matches: List[BOClash] = self._bracket.rounds[self.rounds - 1]

        for idx, bo_clash in enumerate(matches):
            if not hasattr(bo_clash, "winner") or bo_clash.winner is None:
                return ClashInfo(
                    round=self.rounds,
                    index=idx,
                    team1=bo_clash.competitor_a.name,
                    team2=bo_clash.competitor_b.name
                )

        raise RuntimeError(f"All clashes resolved for round {self.rounds}")

    def submit_winner(self, name: str, win_score: int, lose_score: int) -> None:
        if self.rounds == 0 or self._bracket is None:
            raise RuntimeError("Bracket not started")

        # 1) Grab the list of BOClash objects for this round
        matches: list[BOClash] = self._bracket.rounds[self.rounds - 1]

        # 2) Find the first unresolved clash for 'name'
        for bo_clash in matches:
            # treat missing or None as unresolved
            if not hasattr(bo_clash, "winner") or bo_clash.winner is None:
                # check if this clash involves the given name
                a = bo_clash.competitor_a.name
                b = bo_clash.competitor_b.name
                if name in (a, b):
                    # dynamically attach the winner property
                    setattr(bo_clash, "winner", name)
                    setattr(bo_clash, "win_score", win_score)
                    setattr(bo_clash, "lost_score", lose_score)
                    break
        else:
            raise ValueError(f"No unresolved match for '{name}' in round {self.rounds}")

        # 3) Collect winners and advance round if needed
        winners = [getattr(m, "winner", None) for m in matches]
        
        # If all matches have winners, advance to next round
        if all(winner is not None for winner in winners):
            self.rounds += 1
        
        # Check if we've reached the final round
        max_rounds = len(self._bracket.rounds)
        if self.rounds > max_rounds:
            self.rounds = max_rounds
        else:
            # 4) Seed all future rounds with any known winners from their respective previous rounds
            for iterate_round in range(2, max_rounds + 1):  # Start from round 2 (which needs winners from round 1)
                next_round = self._bracket.rounds[iterate_round - 1]
                previous_round = self._bracket.rounds[iterate_round - 2]
                
                for idx, clash in enumerate(next_round):
                    # Calculate indices for the two potential clashes feeding into this clash
                    left_idx = 2 * idx
                    right_idx = 2 * idx + 1
                    
                    # Update competitor_a if we have a winner from the left clash
                    if left_idx < len(previous_round):
                        left_clash = previous_round[left_idx]
                        if hasattr(left_clash, "winner") and left_clash.winner is not None:
                            clash.competitor_a = Competitor(left_clash.winner, "", 0)
                    
                    # Update competitor_b if we have a winner from the right clash
                    if right_idx < len(previous_round):
                        right_clash = previous_round[right_idx]
                        if hasattr(right_clash, "winner") and right_clash.winner is not None:
                            clash.competitor_b = Competitor(right_clash.winner, "", 0)

    def get_winner(self) -> Optional[str]:
        """
        Return the final winner's name if the bracket is complete; otherwise None.
        """
        if self._bracket is None:
            return None
        total_rounds = len(self._bracket.rounds)
        if self.rounds != total_rounds:
            return None
        final_round = self._bracket.rounds[self.rounds - 1]
        if not final_round:
            return None
        final_clash = final_round[0]
        return getattr(final_clash, 'winner', None)

    def generate_standings(self, guild_id: int) -> None:
        """
        Generate match icons and a full bracket diagram under:
          /images/{guild_id}/icons/{{round}}_{{clash_index}}.png
          /images/{guild_id}/bracket/current_standing.png
        Requires rounds > 0. To be implemented.
        """
        rounds: List[List[BOClash]] = self._bracket.rounds

        if self.rounds == 0 or self._gen is None:
            raise RuntimeError("Bracket not started")

        img_gen = ImageGen(f"images/guild_{guild_id}")
        return img_gen.create_bracket(rounds, self.rounds).save("bracket/current_standing.png").get_save_path()


    def generate_win_meme(self, guild_id: int, name: str) -> str:
        # Example usage:
        image_gen = ImageGen(f"images")
        winner = self.get_winner() if self.get_winner() is not None else "New Team Name"
        previous_team_name = os.getenv("PREVIOUS_TEAM_NAME")

        match name:
            case "pass_sword":
                # text 1 coords
                t1x1, t1y1 = 210, 155
                t1x2, t1y2 = t1x1 + 200, t1y1 + 200

                #text 2 coords
                t2x1, t2y1 = 330, 270
                t2x2, t2y2 = t2x1 + 200, t2y1 + 200

                # text 3 coords
                t3x1, t3y1 = 120, 30
                t3x2, t3y2 = t3x1 + 200, t3y1 + 200

                return image_gen.load_image("memes/pass_sword.jpg") \
                    .add_text_to_img("Team Name", t1x1, t1y1, t1x2, t1y2, font_size=20, text_color="white") \
                    .add_text_to_img(f"{previous_team_name}", t2x1, t2y1, t2x2, t2y2, font_size=22, text_color="white") \
                    .add_text_to_img(winner, t3x1, t3y1, t3x2, t3y2, font_size=24, text_color="white") \
                    .set_base_dir(f"images/guild_{guild_id}") \
                    .save("meme_output.png").get_save_path()
            case "hotline_bling":
                # text 1 coords
                t1x1, t1y1 = 650, 90
                t1x2, t1y2 = t1x1 + 500, t1y1 + 400

                #text 2 coords
                t2x1, t2y1 = 650, 700
                t2x2, t2y2 = t2x1 + 500, t2y1 + 400

                return image_gen.load_image("memes/hotline_bling.jpg") \
                    .add_text_to_img(f"{previous_team_name}", t1x1, t1y1, t1x2, t1y2, font_size=70, text_color="black") \
                    .add_text_to_img(f"{winner}", t2x1, t2y1, t2x2, t2y2, font_size=70, text_color="black") \
                    .set_base_dir(f"images/guild_{guild_id}") \
                    .save("meme_output.png").get_save_path()