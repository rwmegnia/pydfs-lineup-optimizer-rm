from typing import Dict
from random import getrandbits, uniform
from pydfs_lineup_optimizer.player import Player
from pydfs_lineup_optimizer.lineup import Lineup
import numpy as np
import pandas as pd
from scipy.stats import norm, gamma
from typing import List,Optional

class BaseFantasyPointsStrategy:
    def get_player_fantasy_points(self, player: Player) -> float:
        raise NotImplementedError

    def set_previous_lineup(self, lineup: Lineup):
        pass


class StandardFantasyPointsStrategy(BaseFantasyPointsStrategy):
    def get_player_fantasy_points(self, player: Player) -> float:
        return player.fppg

    def set_previous_lineup(self, lineup: Lineup):
        pass


class RandomFantasyPointsStrategy(BaseFantasyPointsStrategy):
    def __init__(self, min_deviation: float = 0.0, max_deviation: float = 0.12):
        self.min_deviation = min_deviation
        self.max_deviation = max_deviation

    def get_player_fantasy_points(self, player: Player) -> float:
        if player.fppg_floor is not None and player.fppg_ceil is not None:
            return uniform(player.fppg_floor, player.fppg_ceil)
        multiplier = uniform(
            player.min_deviation if player.min_deviation is not None else self.min_deviation,
            player.max_deviation if player.max_deviation is not None else self.max_deviation
        )
        return player.fppg * (1 + (-1 if bool(getrandbits(1)) else 1) * multiplier)


class ProgressiveFantasyPointsStrategy(BaseFantasyPointsStrategy):
    def __init__(self, scale: float = 0.01):
        self.scale = scale
        self.player_multipliers = {}  # type: Dict[Player, float]

    def get_player_fantasy_points(self, player: Player) -> float:
        if player not in self.player_multipliers:
            self.player_multipliers[player] = 0
        return player.fppg * (1 + self.player_multipliers[player])

    def set_previous_lineup(self, lineup: Lineup):
        lineup_players = set(lineup)
        for player in self.player_multipliers:
            if player in lineup_players:
                self.player_multipliers[player] = 0
            else:
                scale = player.progressive_scale if player.progressive_scale is not None else self.scale
                self.player_multipliers[player] += scale


# class CorrelatedFantasyPointsStrategy(BaseFantasyPointsStrategy):
#     """
#     Generates correlated fantasy point samples using team-level
#     correlation matrices and per-player mean/stdev projections.
#     """

#     def __init__(self, team_corr_df, base_proj_df,
#                  variance_scale=1.0,
#                  game_env_std=0.15,
#                  random_state=None):
    
#         # Clean correlation matrix input
#         corr_df = team_corr_df.copy().reset_index()
#         corr_df["team"] = corr_df["team"].astype(str)
#         corr_df["position_slot"] = corr_df["position_slot"].astype(str)
    
#         # MultiIndex (team, position_slot)
#         self.corr_df = (
#             corr_df
#             .set_index(["team", "position_slot"])
#             .sort_index()
#         )
    
#         # Store base projections for fallback (and for position_slot mapping)
#         self.base_proj_df = base_proj_df.copy()
    
#         self.variance_scale = variance_scale
#         self.game_env_std = game_env_std
#         self.current_world = {}
#         self.rng = np.random.default_rng(random_state)
#         self.optimizer = None
    
#         # ======================================
#         #       ✔ Precompute team cache
#         # ======================================
#         self.team_cache = {}
    
#         for team, tdf in self.base_proj_df.groupby("team"):
#             # Unique per-slot values only
#             uniq = (
#                 tdf.drop_duplicates("position_slot")
#                    .sort_values("position_slot")
#                    .copy()
#             )
    
#             # A team may have no usable rows (rare)
#             if uniq.empty:
#                 continue
    
#             slots = uniq["position_slot"].tolist()
#             mu = uniq["Projection"].values
#             sigma = uniq["stdev_proj"].values * self.variance_scale
    
#             # -------------------------------------
#             # ✔ Extract correlation block safely
#             # -------------------------------------
#             try:
#                 corr_block = self.corr_df.loc[(team, slots), slots]
#                 C = self.nearest_psd(corr_block.values)
#             except Exception:
#                 # Missing team or missing slots in correlation matrix
#                 C = np.eye(len(slots))
    
#             cov = C * np.outer(sigma, sigma)
    
#             # -------------------------------------
#             # ✔ Store everything needed at runtime
#             # -------------------------------------
#             self.team_cache[team] = {
#                 "slots": slots,
#                 "slot_index": {s: i for i, s in enumerate(slots)},
#                 "mu": mu,
#                 "sigma": sigma,
#                 "cov": cov,
#             }



#     # --------------------------------------------------------
#     # Optimizer hookup
#     # --------------------------------------------------------
#     def set_optimizer(self, optimizer):
#         self.optimizer = optimizer

#     # --------------------------------------------------------
#     # PSD helper
#     # --------------------------------------------------------
#     def nearest_psd(self, A, eps=1e-6):
#         A = (A + A.T) / 2
#         vals, vecs = np.linalg.eigh(A)
#         vals[vals < eps] = eps
#         return vecs @ np.diag(vals) @ vecs.T

#     # --------------------------------------------------------
#     # TEAM-LEVEL SAMPLING
#     # --------------------------------------------------------
#     def sample_team_world(self, team):
#         cache = self.team_cache.get(team)
#         if cache is None:
#             return None
#         sims = self.rng.multivariate_normal(cache["mu"], cache["cov"])
#         sims = np.maximum(sims, 0)
#         return sims
    
#     # --------------------------------------------------------
#     # BUILD FULL CORRELATED WORLD FOR ALL PLAYERS
#     # --------------------------------------------------------
#     def build_correlated_world(self, players):
#         world = {}
    
#         # Group players by team without pandas
#         team_groups = {}
#         for p in players:
#             team_groups.setdefault(p.team, []).append(p)
    
#         for team, plist in team_groups.items():
#             cache = self.team_cache.get(team)
    
#             # fallback if no team correlation
#             if cache is None:
#                 print('DURKA')
#                 for p in plist:
#                     world[p.id] = p.fppg
#                 continue
    
#             sims = self.sample_team_world(team)
    
#             slot_to_val = dict(zip(cache["slots"], sims))
    
#             for p in plist:
#                 slot = getattr(p, "position_slot", None)
#                 if slot not in slot_to_val:
#                     world[p.id] = p.fppg
#                 else:
#                     fp = slot_to_val[slot]
#                     # CPT multiplier
#                     if getattr(p, "roster_position", "") == "CPT":
#                         fp *= 1.5
#                     world[p.id] = fp
    
#         return world


#     # --------------------------------------------------------
#     # STRATEGY INTERFACE
#     # --------------------------------------------------------
#     def set_previous_lineup(self, lineup):
#         players = self.optimizer.player_pool.filtered_players
#         self.current_world = self.build_correlated_world(players)

#     def get_player_fantasy_points(self, player):
#         return self.current_world.get(player.id, player.fppg)


# ======================================================
#   NEW: Game-Level Correlated Fantasy Points Strategy
# ======================================================
def _nearest_psd(A: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    A = (A + A.T) / 2.0
    vals, vecs = np.linalg.eigh(A)
    vals = np.clip(vals, eps, None)
    return vecs @ np.diag(vals) @ vecs.T


def _copula_gamma(mu: np.ndarray, sigma: np.ndarray, C: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """
    Gaussian copula + Gamma marginals.
    Ensures positive fantasy points while preserving correlations.
    """
    n = len(mu)
    # 1) Latent correlated normal
    Z = rng.multivariate_normal(mean=np.zeros(n), cov=C)
    # 2) Uniform(0,1)
    U = norm.cdf(Z)
    # 3) Gamma quantiles
    shape = (mu ** 2) / (sigma ** 2 + 1e-9)
    scale = (sigma ** 2) / (mu + 1e-9)
    FP = gamma.ppf(U, a=shape, scale=scale)
    return np.maximum(FP, 0.0)


class CorrelatedFantasyPointsStrategy(BaseFantasyPointsStrategy):
    """
    Game-level correlated fantasy points using:
      - Per-team correlation matrices (including points_team/points_opp)
      - Per-player projections & std. devs
      - Gaussian copula + Gamma marginals (always ≥ 0)

    Expected inputs:
      team_corr_df:
        - DataFrame with MultiIndex ['team', 'position_slot']
        - Columns include your slots + 'points_team', 'points_opp'

      base_proj_df:
        - Columns:
            - id_col (e.g. 'ID') -> matches Player.id
            - 'team', 'game_id', 'position'
            - 'Projection', 'stdev_proj'
            - 'position_slot' (e.g., 'QB1', 'WR2', etc.)
            - 'expected_team_points', 'expected_opp_points', 'team_score_std'
              (same value repeated per row for that team/game)
    """

    def __init__(
        self,
        team_corr_df: pd.DataFrame,
        base_proj_df: pd.DataFrame,
        id_col: str = "ID",
        variance_scale: float = 1.0,
        random_state: Optional[int] = None,
    ):
        self.id_col = id_col
        self.variance_scale = variance_scale
        self.rng = np.random.default_rng(random_state)
        self.optimizer = None
        self.current_world: Dict = {}

        # --- Normalize correlation matrix ---
        corr_df = team_corr_df.copy().reset_index()
        corr_df["team"] = corr_df["team"].astype(str).str.upper().str.strip()
        corr_df["position_slot"] = corr_df["position_slot"].astype(str).str.strip()
        self.corr_df = (
            corr_df
            .set_index(["team", "position_slot"])
            .sort_index()
        )

        # --- Normalize projections DataFrame ---
        df = base_proj_df.copy()
        df["team"] = df["team"].astype(str).str.upper().str.strip()
        df["position_slot"] = df["position_slot"].astype(str).str.strip()

        if "stdev_proj" not in df.columns:
            df["stdev_proj"] = 0.5 * df["Projection"].clip(lower=0)

        # We'll need these later
        self.base_proj_df = df

        # Precompute per-team caches for speed
        self.team_cache: Dict[str, Dict] = {}
        self._build_team_cache()

    # --------------------------------------------------
    # Public API to attach optimizer
    # --------------------------------------------------
    def set_optimizer(self, optimizer):
        self.optimizer = optimizer

    # --------------------------------------------------
    # Build per-team base + correlation slices
    # --------------------------------------------------
    def _build_team_cache(self):
        """
        Precompute for each team:
          - base table with virtual points_team / points_opp rows
          - list of slots
          - common_s: slots that appear in correlation matrix
          - mu, sigma, C used for copula-gamma sampling
        """
        df = self.base_proj_df

        if not {"expected_team_points", "expected_opp_points", "team_score_std"}.issubset(df.columns):
            # If these are missing, we just won't add the team-level rows.
            has_team_points = False
        else:
            has_team_points = True

        for team, tdf in df.groupby("team"):
            # Use one representative row to get team-level stats if available
            if has_team_points:
                ref = tdf.iloc[0]
                team_for = float(ref["expected_team_points"])
                team_against = float(ref["expected_opp_points"])
                team_std = float(ref["team_score_std"])
                team_std = max(team_std, 0.1)
                opp_std = float(ref['opp_score_std'])
                opp_std = max(opp_std, 0.1)
            else:
                team_for = None
                team_against = None
                team_std = None

            # Base: per-slot rows
            base = tdf[[
                self.id_col,
                "position_slot",
                "Projection",
                "stdev_proj",
                "team",
                "position",
                "game_id",
            ]].copy()

            base = base.drop_duplicates("position_slot").set_index("position_slot")

            # Add virtual slots for team points if available
            if has_team_points:
                team_row = pd.DataFrame([{
                    self.id_col: f"{team}_TEAM_FOR",
                    "Projection": team_for,
                    "stdev_proj": team_std,
                    "team": team,
                    "position": "TEAM_FOR",
                    "game_id": base["game_id"].iloc[0],
                }], index=["points_team"])

                opp_row = pd.DataFrame([{
                    self.id_col: f"{team}_TEAM_AGAINST",
                    "Projection": team_against,
                    "stdev_proj": opp_std,
                    "team": team,
                    "position": "TEAM_AGAINST",
                    "game_id": base["game_id"].iloc[0],
                }], index=["points_opp"])

                base = pd.concat([base, team_row, opp_row], axis=0)

            slots = base.index.tolist()

            # Which slots exist in correlation matrix for this team?
            try:
                team_slots_available = self.corr_df.loc[team].index.unique().tolist()
            except KeyError:
                team_slots_available = []

            common_s = [s for s in slots if s in team_slots_available]

            if len(common_s) == 0:
                # No correlation info → independent sampling
                C = np.eye(len(slots))
                mu = base["Projection"].values
                sigma = (base["stdev_proj"].values * self.variance_scale)
                independent = True
            else:
                # Build mu/sigma only for common slots
                mu = base.loc[common_s, "Projection"].values
                sigma = base.loc[common_s, "stdev_proj"].values * self.variance_scale

                # Correlation block
                C = self.corr_df.loc[(team, common_s), common_s].fillna(0).values
                C = _nearest_psd(C)
                independent = False

            self.team_cache[team] = {
                "base": base,
                "slots": slots,
                "common_s": common_s,
                "mu": mu,
                "sigma": sigma,
                "C": C,
                "independent": independent,
            }

    # --------------------------------------------------
    # Build one "world" of correlated projections
    # --------------------------------------------------
    def _build_correlated_world(self, players: List[Player]) -> Dict:
        """
        Construct a dict mapping player_id -> correlated fantasy points
        for this "world".
        """
        # Build a quick lookup of which DFS players are actually in the current pool.
        player_ids = {p.id for p in players}

        world_rows = []

        for team, cache in self.team_cache.items():
            base = cache["base"].copy()
            slots = cache["slots"]
            common_s = cache["common_s"]
            mu = cache["mu"]
            sigma = cache["sigma"]
            C = cache["C"]
            independent = cache["independent"]

            if len(slots) == 0:
                continue

            if len(common_s) == 0 or independent:
                # Independent gamma sampling across slots
                mu_ind = base["Projection"].values
                sigma_ind = (base["stdev_proj"].values * self.variance_scale)
                C_ind = np.eye(len(mu_ind))
                sampled = _copula_gamma(mu_ind, sigma_ind, C_ind, self.rng)
                base["corr_fp"] = sampled
            else:
                # Correlated sampling for common slots
                sampled_common = _copula_gamma(mu, sigma, C, self.rng)
                sample_map = dict(zip(common_s, sampled_common))

                # Fill in all slots
                full_sample = []
                for s in slots:
                    if s in sample_map:
                        full_sample.append(sample_map[s])
                    else:
                        full_sample.append(base.loc[s, "Projection"])
                base["corr_fp"] = full_sample

            # Filter only rows that correspond to real DFS players in this slate
            # (ignore virtual TEAM_FOR/AGAINST rows)
            base_reset = base.reset_index()
            base_reset = base_reset[base_reset[self.id_col].isin(player_ids)]
            world_rows.append(base_reset)

        if not world_rows:
            return {}

        world_df = pd.concat(world_rows, ignore_index=True)

        # Optional: CPT boosting if roster_position is available in base_proj_df
        # (You can adjust this depending on how you store CPT/FLEX info.)
        for col in ["roster_position", "Roster Position"]:
            if col in self.base_proj_df.columns:
                rp = (
                    self.base_proj_df[[self.id_col, col]]
                    .drop_duplicates(self.id_col)
                    .set_index(self.id_col)
                )
                world_df = world_df.merge(
                    rp, left_on=self.id_col, right_index=True, how="left"
                )
                # Apply 1.5x boost to CPT
                mask_cpt = world_df[col].astype(str).str.contains("CPT", na=False)
                world_df.loc[mask_cpt, "corr_fp"] *= 1.5
                break  # only apply once

        # Build final mapping from player_id to corr_fp
        # Ensure IDs line up with Player.id (int/str handling)
        id_series = world_df[self.id_col]
        fp_series = world_df["corr_fp"]
        return dict(zip(id_series, fp_series))

    # --------------------------------------------------
    # Strategy interface
    # --------------------------------------------------
    def set_previous_lineup(self, lineup: Optional[Lineup]):
        """
        Called once before each new lineup is generated.
        We ignore the previous lineup and just build a fresh
        correlated world for all players in the optimizer pool.
        """
        if self.optimizer is None:
            raise ValueError(
                "Optimizer not attached to CorrelatedFantasyPointsStrategy. "
                "Call strategy.set_optimizer(optimizer) after creating the optimizer."
            )
        players = list(self.optimizer.player_pool.filtered_players)
        self.current_world = self._build_correlated_world(players)

    def get_player_fantasy_points(self, player: Player) -> float:
        """
        Return the correlated projection for the current world.
        Fallback to player's base fppg if missing.
        """
        return self.current_world.get(player.id, player.fppg)


    
    