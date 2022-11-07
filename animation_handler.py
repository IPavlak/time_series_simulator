import matplotlib.animation as animation

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
        print("callback", args[0].core_data_idx)
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


    # TODO: check speed - it is actually running slower :(
    def _draw_frame(self, framedata):
        ''' 
        Call the func with framedata and args. If blitting is desired,
        func needs to return a sequence of any artists that were modified.
        '''
        new_artists = self._func(framedata)

        # clear background to start blitting if not clean already
        if not self._clean_bg or len(self._drawn_artists) != len(new_artists):
            print("cleaning bg")
            self._clean_bg = True
            
            for a in self._drawn_artists:
                a.set_animated(False)
            for a in new_artists:
                a.set_animated(True)

            self._fig.canvas.draw_idle()
            self._fig.canvas.flush_events() # enforcing to draw whole frame right now before blitting

            self._blit_cache.clear()  # clear cached background - trigger saving new background

        self._drawn_artists = new_artists

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
        # it has to be cleaned before blitting can start - otherwise we will have those artists in each frame
        self._clean_bg = False
        


    def new_frame_seq(self):
        ''' Use the generating function to generate a new frame sequence '''
        # Since framedata will be passed through function call this is not used
        return lambda: iter(range(100))


    def _blit_draw(self, artists):
        # Handles blitted drawing, which renders only the artists given instead
        # of the entire figure.
        updated_ax = {a.axes for a in artists}
        # Enumerate artists to cache axes' backgrounds. We do not draw
        # artists yet to not cache foreground from plots with shared axes
        for ax in updated_ax:
            # If we haven't cached the background for the current view of this
            # axes object, do so now. This might not always be reliable, but
            # it's an attempt to automate the process.
            cur_view = ax._get_view()
            view, bg = self._blit_cache.get(ax, (object(), None))
            if cur_view != view:
                self._blit_cache[ax] = (
                    cur_view, ax.figure.canvas.copy_from_bbox(ax.get_figure().bbox))    # changed this line to support blitting x and y labels
        # Make a separate pass to draw foreground.
        for a in artists:
            a.axes.draw_artist(a)
        # After rendering all the needed artists, blit each axes individually.
        for ax in updated_ax:
            ax.figure.canvas.blit(ax.clipbox)       # changed this line to support blitting x and y labels