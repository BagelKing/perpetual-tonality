# To do:
#   
# Lilypond notation output
# The rest of the fucking game
# Surface.convert() is run for surface objects to save drawing time because
# PyGame otherwise runs .convert() on every blit

import pygame, sys, random
from pygame.locals import *

pygame.init()
clock = pygame.time.Clock()

width,height = 650,600
wsize = (width,height)

window = pygame.display.set_mode(wsize)
window.fill((125,125,125))
pygame.display.set_caption('Game Prototype')
pygame.display.update()

# Game Objects ----------------------------------------------------------------------

activeObjects = pygame.sprite.Group() # group of objects to run update() every frame
drawObjects = pygame.sprite.Group() # group of objects to be drawn every frame
dirtyRects = [] # list of rects that have been altered on screen

class Object(pygame.sprite.Sprite):
    """Base class for all game objects"""
    def __init__(self,pos=(0,0),img="",rect=""):
        pygame.sprite.Sprite.__init__(self)
        self.pos = pos
        if img is not "": # if img is anything other than an empty string
            if type(img) is pygame.Surface: # if img is a pygame image
                self.image = img.convert() # .convert() saves drawing time
            elif type(img) is str: # else if img is a string
                try: # try using img as a file location
                    self.image = pygame.image.load(img).convert()
                except: # if, for any reason, this fails, mock the user
                    print 'My God, what were you trying to DO?'
            if rect == "":
                self.rect = self.image.get_rect() # use image-generated rect
                self.rect.center = self.pos # position rect at pos
            elif type(rect) is pygame.Rect:
                self.rect = rect # assign existing rect
            self.add(drawObjects) # Add to group containing drawn objects
        self.add(activeObjects) # Add to group containing all active objects
    def clean(self):
        """Place a patch of background over the sprite; should be run before
        drawing"""
        patch = pygame.surface.Surface((self.rect.width,self.rect.height)).convert()
        # ^ Generate surface using the dimensions of rect
        patch.fill((125,125,125)) # Fill patch with gray
        window.blit(patch,self.rect) # Blit to window
        dirtyRects.append(Rect(self.rect.topleft,(self.rect.height,self.rect.width)))
        # ^ Add to portion of screen to be updated
    def on_collide(self):
        """Perform on collision with player"""
        pass

class Player(Object):
    """Player-controlled pixie, guided by the mouse"""
    def __init__(self,pos=(100,height/2)): # position vertically center
        pygame.mouse.set_visible(False) # set mouse invisible
        pygame.mouse.set_pos(pos) # set mouse at pos
        playerSrf = pygame.surface.Surface((5,5)).convert()
        playerSrf.fill((0,255,0))
        Object.__init__(self,pos,"defSprite.bmp")
    def update(self):
        dist = pygame.mouse.get_pos()[1]-self.pos[1] # get interval of mouse movement
        dim = Grid.dimensions() # size of a grid space
        if dist > dim or (-dist) > dim: # if mouse movement is greater than dim
            if dist < 0: dist = -dim # if movement negative, reduce to dim in negative direction
            else: dist = dim # if movement positive, reduce to dim in positive direction
            self.pos = (100,self.pos[1]+dist) # move pos to new location
            pygame.mouse.set_pos(self.pos) # move mouse to new location
        # ^ To prevent Player skipping over notes
        else:
            self.pos = (100,self.pos[1]+dist) # move pos to new location
        self.rect.center = self.pos # update rect to pos (image is placed using rect)
        dirtyRects.append(self.rect)

class Grid(Object):
    """Moving grid that contains objects other than Player"""
    @staticmethod
    def dimensions():
        """Get value for height and width of grid spaces (fit exactly 24x24 onscreen)"""
        return height/24
    def __init__(self):
        Object.__init__(self)
        self.mapping = [] # empty list to be filled with columns (lists) of rects
        dimension = Grid.dimensions() # get dimensions to use
        xHopper = -dimension # begin one space to the left of (0,0) for buffer column
        for x in range((width/dimension)+2): # number of spaces that will fit horizontally,
            column = [] # plus 2
            yHopper = 0 # begin at top of screen
            for y in range(24):
                column.append(pygame.Rect((xHopper,yHopper),(dimension,dimension)))
                # ^ add rect with topleft at (xHopper,yHopper) and ^ dimensions
                yHopper += dimension # hop by one space vertically
            self.mapping.append(column) # add column to mapping
            xHopper += dimension # hop by one space horizontally
    def loop(self,column):
        """Shift grid spaces to the very right edge when they are offscreen left"""
        if column[0].bottomright[0] < 0:
            for q in column: # for each rect in column
                q.topleft = (self.mapping[len(self.mapping)-1][column.index(q)].topright[0]+1,
                             q.topleft[1]) # move to the right of the very last rects
            self.mapping.append(self.mapping.pop(0)) # move column to end of mapping
            for x in drawObjects:
                if x.rect in self.mapping[len(self.mapping)-1]:
                    x.kill() # kill sprites when they go offscreen
            Note(Scale.genScale('c','maj')[int(random.random()*7)],self)
    def move(self):
        for pimu in self.mapping:
            self.loop(pimu)
            for haju in pimu:
                haju.topleft = (haju.topleft[0]-2,haju.topleft[1])
                #pygame.draw.rect(window,(120,0,0),haju,3)

class Note(Object):
    """Object that sounds a designated pitch following collision with Player"""
    def __init__(self,tone,grid): # tone = q' (with notation)
        space = grid.mapping[0][0] # Example space to get dimensions
        self.tone = tone
        noteSrf = pygame.surface.Surface((space.height,space.width))
        noteSrf.fill((200,100,100)) # create new surface for Note from space dimensions
        pygame.draw.rect(noteSrf,(100,200,100),noteSrf.get_rect(),3) # draw rect to noteSrf
        if tone not in sounds:
            if tone+"'" in sounds:
                tone += "'"
            else:
                pass # Should gracefully cancel creation of note
        self.sound = sounds[tone]
        print tone,self.sound
        Object.__init__(self,img=noteSrf,rect=grid.mapping[len(grid.mapping)-1]
                        [chromatic.index(tone[0])]) # assign vertical position by tone
    def update(self):
        dirtyRects.append(self.rect)
    def on_collide(self):
        """Play note and destroy self"""
        try:
            pygame.mixer.find_channel().play(self.sound)
        except:
            print "SOUND FAILURE: "+self.tone
        print self.sound
        self.kill() # Remove Sprite from all groups

# Music Control Objects -------------------------------------------------------------

class Scale:
    """Class for scale structures (not game object)"""
    def __init__(self,tonic='c',mode='maj'):
        self.scale = Scale.genScale(tonic,mode)
        self.tonic = tonic
        self.mode = mode
    @staticmethod
    def genScale(tonic,mode):
        """Return the given scale for the given tonic in a list"""
        tonic = tonic.lower() # chromatic uses lowercase characters
        if tonic not in chromatic: # if tonic is not a valid musical note
            return False
        if mode not in modes: # if mode is not in the modes dictionary
            mode = 'maj' # use major scale by default
        fScale = []
        chromaticExtended = chromatic+chromatic
        # ^ Allow for reaching the end of chromatic and resuming from the beginning
        x = chromaticExtended.index(tonic)
        for wallabee in modes[mode]:
                      # ^ gets increments for given scale
            x += wallabee # move through chromatic by the specified increment
            fScale.append(chromaticExtended[x])
        fScale.insert(0,fScale.pop()) # place tonic at beginning
        return fScale
    @staticmethod
    def getAllScales():
        """Yield all scales (that are dealt with by this program)"""
                 # v (below) a global list should be made for these
        for a in ['maj','nmin','hmin','jmin']: # for each scale mode
            for b in chromatic: # for each note in the chromatic scale
                yield Scale.genScale(b,a) # yield scale b in mode a

class Chord:
    """Classs for chord structures (not game object)"""
    def __init__(self,scale,root):
        self.scale = scale.scale
        scaleExt = scale.scale+scale.scale # allow for continuation from start
        self.chord = [scaleExt[root-1],scaleExt[root+1],scaleExt[root+3]]
        # ^ Generate triad

class MusicControl(Object):
    """Responsible for the generation of music"""
    @staticmethod
    def getCompatibleScales(notes):
        """Return all scales containing all items in notes"""
        cScales = []
        for a in scales: # for each scale
            cScales.append(a) # add scale to cScales
            for b in notes: # for each note
                if b not in a: # if note not in scale
                    cScales.remove(a) # remove scale
                    break # move to next scale

        # This is done in a bit of a backwards way because notes does not #
        # have a definite length and this approach accomodates any length #

        return tuple(cScales)
    @staticmethod
    def getTriad(scale):
        return [scale[0],scale[2],scale[4]]

class SoundControl(Object):
    """Control the PyGame Mixer module"""
    def __init__(self,vol=1.0):
        Object.__init__(self)
        self.vol = vol
    def set_vol(self):
        """Apply self.vol to all sound channels"""
        for a in range(pygame.mixer.get_num_channels()): # for a in list of channel IDs
            pygame.mixer.Channel(a).set_volume(self.vol) # set Channel(a) volume to self.vol
    def update(self):
         for event in pygame.event.get():
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 5: # if scroll wheel down
                    print "Scroll Wheel Down"
                    if self.vol > 0.0: # if volume is not 0
                        self.vol -= 0.1 # reduce volume by 0.1
                        self.set_vol() # apply new volume to all channels
                elif event.button == 4: # else if scroll wheel up
                    print "Scroll Wheel Up"
                    if self.vol < 1.0: # if volume is not max
                        self.vol += 0.1 # increase volume by 0.1
                        self.set_vol() # apply new volume to all channels

# Data Constants --------------------------------------------------------------------

chromatic = ('c','c#','d','d#','e','f',
             'f#','g','g#','a','a#','b')
modes = {'maj': (2,2,1,2,2,2,1),'nmin': (2,1,2,2,1,2,2),
         'hmin': (2,1,2,2,1,3,1),'jmin': (2,1,2,2,2,2,1)}
scales = tuple([x for x in Scale.getAllScales()])
sounds = {"c'": pygame.mixer.Sound("c'.wav"), "c#'": pygame.mixer.Sound("c#'.wav"),
          "d'": pygame.mixer.Sound("d'.wav"), "d#'": pygame.mixer.Sound("d#'.wav"),
          "e'": pygame.mixer.Sound("e'.wav"), "f'": pygame.mixer.Sound("f'.wav"),
          "f#'": pygame.mixer.Sound("f#'.wav"), "g'": pygame.mixer.Sound("g'.wav"),
          "g#'": pygame.mixer.Sound("g#'.wav"), "a'": pygame.mixer.Sound("a'.wav"),
          "a#'": pygame.mixer.Sound("a#'.wav"), "b'": pygame.mixer.Sound("b'.wav")}

# Game Initialization ---------------------------------------------------------------

compats = []
compatScales = MusicControl.getCompatibleScales(['a','f#','d','e'])
print compatScales
for a in compatScales:
    for b in a:
        if b not in compats:
            compats.append(b)
compats.sort()
print compats
print scales
flimmy = Player()
valjean = SoundControl(0.5)
valjean.set_vol()
raga = Grid()
pygame.mixer.init()
stimpy = Note(tone='b',grid=raga)

def gameloop():
    for event in pygame.event.get():
        #print event
        if event.type == QUIT:
            pygame.quit()
            #sys.exit()
            break

    for a in drawObjects.sprites():
        a.clean() # clear sprites
    raga.move() # move grid
    activeObjects.update() # update active objects
    for x in pygame.sprite.spritecollide(flimmy,drawObjects,False):
        # ^ for objects colliding with player
        x.on_collide() # perform collision events
    drawObjects.draw(window) # draw sprites

    pygame.display.update(dirtyRects) # update areas of screen that have changed
    clock.tick(60)

    for i in dirtyRects: dirtyRects.remove(i) # emtpy dirtyRects
    
while True:
    gameloop()
