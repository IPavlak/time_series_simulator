import matplotlib.animation as animation
from time import sleep
import threading

class EventSource:
    def __init__(self):
        self.func = None
        self.running = False
    
    def add_callback(self, func):
        self.func = func
    
    def remove_callback(self, *args):
        self.func = None
    
    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def is_running(self):
        return self.running

    def call(self, done_event, *args):
        print("callback", *args)
        if self.running and self.func is not None:
            self.func(*args)
            done_event.set()

        if not self.running:
            print("[EventSource] Trying to run callback while not running, "
                  "call start() to start event source")
        if self.func is None:
            raise RuntimeError("[EventSource] Callback was not set")

    
class AnimationHandler(animation.Animation):
    def __init__(self, fig, func, init_func=None, blit=True):
        self._func = func
        self._init_func = init_func

        animation.Animation.__init__(self, fig, event_source=EventSource(), blit=blit)

    
    def _step(self, framedata):
        '''
        Handler for getting events. By default, gets the next frame in the
        sequence and hands the data off to be drawn.
        '''
        # Returns True to indicate that the event source should continue to
        # call _step, until the frame sequence reaches the end of iteration,
        # at which point False will be returned.
        try:
            self._draw_next_frame(framedata, self._blit)
            return True
        except:
            return False


    def _draw_frame(self, framedata):
        ''' 
        Call the func with framedata and args. If blitting is desired,
        func needs to return a sequence of any artists that were modified.
        '''
        # clear background to start blitting if not clean already
        if not self._clean_bg:
            print("cleaning bg", framedata)
            self._clean_bg = True
            for a in self._drawn_artists:
                a.set_animated(True)
            self._fig.canvas.draw_idle()
            self._fig.canvas.flush_events() # enforcing to draw whole frame right now before blitting

        self._drawn_artists = self._func(framedata)

        if self._blit:
            if self._drawn_artists is None:
                raise RuntimeError('The animation function must return a '
                                   'sequence of Artist objects.')
            self._drawn_artists = sorted(self._drawn_artists,
                                        key=lambda x: x.get_zorder())

            # if animated, artist is excluded from regular drawing with draw() or draw_idle()
            # you have to call Axes.draw_artist() or Figure.draw_artist() explicitly on an artist
            for a in self._drawn_artists:
                a.set_animated(self._blit)

    def _init_draw(self):
        ''' 
        Initialize the drawing either using the given init_func or by
        calling the draw function with the first item of the frame sequence.
        For blitting, the init_func should return a sequence of modified
        artists.
        '''
        # Used on resize !!!!
        print("init draw")
        self._drawn_artists = self._init_func()
        if self._blit:
            if self._drawn_artists is None:
                raise RuntimeError('The animation init function must return a '
                                    'sequence of Artist objects.')
            self._drawn_artists = sorted(self._drawn_artists,
                                        key=lambda x: x.get_zorder())

        # draw_idle() excludes animated artists to support blitting
        # draw artists given in _init_func() and keep them on figure after draw_idle()
        for a in self._drawn_artists:
            a.set_animated(False)
        # self._fig.canvas.draw_idle()

        # background is not clear now because of the artists drawn with draw_idle
        # it has to be cleaned before blitting can start - otherwise we will have thos artists in each frame
        self._clean_bg = False
        


    def new_frame_seq(self):
        ''' Use the generating function to generate a new frame sequence '''
        # Since framedata will be passed through function call this is not used
        return lambda: iter(range(100))