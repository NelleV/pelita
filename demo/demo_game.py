#!/usr/bin/python
from pelita.game_master import GameMaster
from pelita.player import StoppingPlayer, SimpleTeam
from pelita.viewer import AsciiViewer
from players import RandomPlayer, NQRandomPlayer

if __name__ == '__main__':
    layout = (
        """ ##################
            #0#.  .  # .     #
            #2#####    #####1#
            #     . #  .  .#3#
            ################## """)
    teams = [
        SimpleTeam(StoppingPlayer(), NQRandomPlayer()),
        SimpleTeam(StoppingPlayer(), NQRandomPlayer())
    ]
    gm = GameMaster(layout, teams, 4, 200)
    gm.register_viewer(AsciiViewer())
    gm.play()
