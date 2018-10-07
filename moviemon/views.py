
import os
import pickle

from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse

from .classes.games import Games


def _information_savefile(game):
  result = _information(game)
  result['saves'] = {'a': {}, 'b': {}, 'c': {}}
  list_dirs = os.listdir(settings.BASE_SAVE)

  for d in list_dirs:
    with open(settings.BASE_SAVE + d, 'rb') as fd:
      file = pickle.load(fd)

      result['saves'][file['name']] = {
          'moviedex': len(file['moviedex']),
          'moviemon': len(file['moviemon']),
      }

      fd.close()
  return result


def _information(game, id=None):
  result = game.get_map()
  result['movieballs'] = game.get_movieballs()
  result['strength'] = game.get_strength()
  result['moviedex_nb'] = len(game.get_moviedex())

  if id is not None:
    result['info_event'] = game.get_movie_id(id)
  else:
    result['info_event'] = game.get_info_event()

  return result


def load_pickle():
  game = Games()

  with open(settings.BASE_TMP + 'savefile', 'rb') as fd:
    game.load(pickle.load(fd))
    fd.close()

  return game

def save_pickle(game):
  with open(settings.BASE_TMP + 'savefile', 'wb') as fd:
    pickle.dump(game.dump(), fd)
    fd.close()


def init(request):
  game = Games()
  game.load_default_settings()

  result = _information(game)

  save_pickle(game)

  # return render(request, 'index.html', result)
  context = {
    'button': {
      'a': '/worldmap',
      'b': '/load',
      'start': '/moviedex/',
      'select': '/option'
    },
    'event': {
      'film': 'test'
    }
  }

  return render(request, 'TitleScreen.html', context)


def worldmap(request):
  game = load_pickle()

  result = _information(game)

  if 'direction' in request.GET:
    moved = False

    if request.GET['direction'] == 'left':
      moved = game.move_left()
    if request.GET['direction'] == 'right':
      moved = game.move_right()
    if request.GET['direction'] == 'down':
      moved = game.move_down()
    if request.GET['direction'] == 'up':
      moved = game.move_up()


    if moved == True:
      evt = game.event()
    else:
      evt = game.get_event()

    result = _information(game)
    result['event'] = evt

  save_pickle(game)

  return render(request, 'index.html', result)


def moviedex(request, id):
  game = load_pickle()

  result = _information(game)

  if id and game.isExisting(id) and game.isCatch(id) is True:
    result['details'] = game.get_movie_id(id)
    context = {
        'button': {
          'b': '/moviedex/',
        },
        'data': {
          'details': result['details'] if 'details' in result else None
        },
        'event': {
          'film': 'test'
        }
    }
  else:
    id = request.GET['id'] if 'id' in request.GET else None
    result['moviedex'] = game.get_moviedex()

    if id is not None:
      for idx, m in enumerate(result['moviedex']):
        if id == m:
          movie = m
          prev = ('/moviedex/?id=' + result['moviedex'][idx - 1]) if (idx - 1) >= 0 else '/moviedex/'
          suiv = ('/moviedex/?id=' + result['moviedex'][idx + 1]) if (idx + 1) < len(result['moviedex']) else '/moviedex/?id=' + result['moviedex'][idx]
          break
    else:
      movie = result['moviedex'][:1][0] if len(result['moviedex'][:1]) > 0 else None
      prev = ''
      suiv = ('/moviedex/?id=' + result['moviedex'][1:2][0]) if len(result['moviedex'][1:2]) > 0 else ''

    context = {
      'button': {
        'a': '/moviedex/' + movie,
        'select': '/worldmap/',
        'left': prev,
        'right': suiv
      },
      'data': {
        'moviemon_id': movie if movie else None,
        'details': result['details'] if 'details' in result else None
      },
      'event': {
        'film': 'test'
      }
    }

  save_pickle(game)

  return render(request, 'MovieDex.html', context)


def battle(request, id):
  game = load_pickle()

  if id and game.isCatch(id) is False:
    context = _information(game, id)

    if game.get_movieballs() <= 0:
      context['info_event']['text'] = 'Ha les boules, il n\'a plus de movieballs'
      context['button'] = {
        'a': '/worldmap/',
        'b': '/worldmap/'
      }
    elif 'first' not in request.GET:
      catched = game.try_catch(id)
      context['info_event']['text'] = 'Oui je l\'ai eu !!!' if catched == True else 'HAAA j\'ai louper mon coup'
      context['button'] = {
        'a': '/worldmap/' if catched == True else '/battle/' + id,
        'b': '/worldmap/'
      }
    else:
      context['info_event']['text'] = 'haut les mains voyous'
      context['button'] = {
        'a': '/battle/' + id,
        'b': '/worldmap/'
      }

    save_pickle(game)

    return render(request, 'Battle.html', context)
    # return render(request, 'index.html', result)
  return HttpResponse('Id not conform.')


def options(request):
  return HttpResponse('OK')


def save_game(request, slot=None):
  game = load_pickle()

  if not os.path.exists(settings.BASE_SAVE):
    os.makedirs(settings.BASE_SAVE)

  list_dirs = os.listdir(settings.BASE_SAVE)

  if slot is not None and slot in ['a', 'b', 'c']:
    nb_moviedex = len(game.get_moviedex())
    nb_moviemon = len(game.get_movie())
    new_name = settings.BASE_SAVE + 'slot' + slot + \
        '_' + str(nb_moviedex) + '_' + str(nb_moviemon)

    for d in list_dirs:
      if slot == d[4:5]:
        os.rename(settings.BASE_SAVE + d, new_name)

    with open(new_name, 'wb') as fd:
      result = game.dump()
      result['name'] = slot
      pickle.dump(result, fd)
      fd.close()

  # information on slots
  result = _information_savefile(game)
  result['saves_route'] = 'save_game'
  save_pickle(game)

  return render(request, 'index.html', result)


def load_game(request, slot=None):
  game = load_pickle()

  if not os.path.exists(settings.BASE_SAVE):
    os.makedirs(settings.BASE_SAVE)

  list_dirs = os.listdir(settings.BASE_SAVE)

  if slot is not None and slot in ['a', 'b', 'c']:
    for d in list_dirs:
      if slot == d[4:5]:
        with open(os.path.join(settings.BASE_SAVE, d), 'rb') as fd:
          game.load(pickle.load(fd))
          fd.close()

  # information on slots
  result = _information_savefile(game)
  result['saves_route'] = 'load_game'
  save_pickle(game)

  return render(request, 'index.html', result)
