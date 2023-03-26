# The Wall is Down: 1989-2014
> _1989. Cold war is over. The Berlin wall is down. URSS breaks into pieces and USA
becomes the global superpower. However, the world is not totally polarized. New
powers acquire nuclear weapons: France, UK, Israel, India, Pakistan. China adopts a
more active role. Russia is still a relevant factor and Europe joins into a common
but hard to coordinate agenda.
25 years since the wall fell, the cold war has become global, muti-modal, and
more complex than ever._

The Wall is Down is a 1-4 player game of geopolitics inspired in Twilight Struggle.
* bundle has all the components you need to play the game: rules, board, cards and tokens. Just print them and use some color cubes and a 6-sided dice. NOTE: this version may be out of sync with the developer version (bundleRW), from which you can generate all the final files.
* bunbleRW has the original files if you want to translate, change or improve the game. This is the latest version of the game.
* TWID-SOA is the REST API for the game. It's still under development but it's mostly functional (more info below).

The game is provided under a CC-BY license (see the rules for more info about that)
Initially the game was discussed in this [BGG forum](https://boardgamegeek.com/thread/2842384/wall-down-1989-2014-ts-game-4-players)

Some screenshots of the prototype:
![Screenshot of TWID.](https://cf.geekdo-images.com/R6bD6NbnSrdbohP-IjG_lA__imagepage/img/5rqR31ez6eKelOG7JhKT9BW3XTQ=/fit-in/900x600/filters:no_upscale():strip_icc()/pic6874852.jpg)
![S2](https://cf.geekdo-images.com/mNGYFWINaahDzpUHnYullw__medium/img/J0V7TKdkDbKWnWKFE_OQ9L09ahU=/fit-in/500x500/filters:no_upscale():strip_icc()/pic6874857.jpg)

### BUNDLE RW
The contents are:
* _board.svg_: a file edited with Inkscape but allegedly editable with any Photoshop-like program. There's a boardExtra.svg with tokens for card texts that remain in play, UE expansions, veto/ahead tokens and the like.
* _cards.ods_: a spreadsheet with the card texts and some other sheets with statistics on the cards. I use the first sheet, exported as csv, with [Hccd card designer](https://github.com/vaemendis/hccd), to generate the pdf with the cards.
* _rules.docx_:, a text document with the rules.

### REST API

In order to run the server, use:
```
sudo docker-compose -f docker-compose.yml up --build --remove-orphans --force-recreate
```

The folder frontend contains a script test.py that emulates all the API endpoint calls for a full game. There's also a Swagger documentation at https://localhost/docs after deploying the docker container. There is no graphical frontend yet.
