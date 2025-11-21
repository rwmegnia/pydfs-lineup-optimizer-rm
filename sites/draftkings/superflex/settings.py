from pydfs_lineup_optimizer.settings import BaseSettings, LineupPosition
from pydfs_lineup_optimizer.constants import Sport, Site
from pydfs_lineup_optimizer.sites.sites_registry import SitesRegistry
from pydfs_lineup_optimizer.lineup_printer import IndividualSportLineupPrinter
from pydfs_lineup_optimizer.sites.draftkings.superflex.importer import DraftKingsCSVImporter


class DraftKingsSuperflexSettings(BaseSettings):
    site = Site.DRAFTKINGS_SUPERFLEX
    budget = 50000
    max_from_one_team = 8
    csv_importer = DraftKingsCSVImporter


@SitesRegistry.register_settings
class DraftKingsFootballSuperflexSettings(DraftKingsSuperflexSettings):
    sport = Sport.FOOTBALL
    min_games = 2
    positions = [
        LineupPosition('QB', ('QB',)),
        LineupPosition('RB', ('RB',)),
        LineupPosition('RB', ('RB',)),
        LineupPosition('WR', ('WR',)),
        LineupPosition('WR', ('WR',)),
        LineupPosition('TE', ('TE',)),
        LineupPosition('FLEX', ('WR', 'RB', 'TE')),
        LineupPosition('S-FLEX', ('QB','RB','WR','TE'))
    ]



