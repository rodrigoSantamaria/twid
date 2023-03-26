# The Wall is Down: 1989-2014
> _1989. Cold war is over. The Berlin wall is down. URSS breaks into pieces and USA
becomes the global superpower. However, the world is not totally polarized. New
powers acquire nuclear weapons: France, UK, Israel, India, Pakistan. China adopts a
more active role. Russia is still a relevant factor and Europe joins into a common
but hard to coordinate agenda.
25 years since the wall fell, the cold war has become global, muti-modal, and
more complex than ever._

The Wall is Down is a 1-4 player game of geopolitics inspired in Twilight Struggle.
* bundle has all the components you need to play the game: rules, board, cards and tokens. Just print them and use some color cubes and a 6-sided dice.
* bunbleRW has the original files if you want to translate, change or improve the game.
* TWID-SOA is the REST API for the game. It's still under development but it's mostly functional (more info below).

The game is provided under a CC-BY license (see the rules for more info about that)

### REST API

In order to run the server, use:
```
sudo docker-compose -f docker-compose.yml up --build --remove-orphans --force-recreate
```

The folder frontend contains a script test.py that emulates all the API endpoint calls for a full game. There's also a Swagger documentation at https://localhost/docs after deploying the docker container.
