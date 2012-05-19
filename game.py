# To do:
# Lilypond notation output
# Musical notes
# Collision checks
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

# Game Objects ----------------------------------------------------------------------

activeObjects = pygame.sprite.Group() # group of objects to run update() every frame
drawObjects = pygame.sprite.Group() # group of objects to be drawn every frame

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

class Player(Object):
    """Player-controlled pixie, guided by the mouse"""
    def __init__(self,pos=(100,height/2)): # position vertically center
        pygame.mouse.set_visible(False) # set mouse invisible
        pygame.mouse.set_pos(pos) # set mouse at pos
        Object.__init__(self,pos,"defSprite.bmp")
    def update(self):
        self.pos = (100,pygame.mouse.get_pos()[1]) # set pos to (100,mouse-y)
        self.rect.center = self.pos # update rect to pos (image is placed using rect)

class Grid(Object):
    """Moving grid that contains objects other than Player"""
    def __init__(self):
        Object.__init__(self)
        self.mapping = [] # empty list to be filled with columns (lists) of rects
        dimension = height/24 # value for height and width of grid spaces (create exactly 24)
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
    def move(self):
        for pimu in self.mapping:
            self.loop(pimu)
            for haju in pimu:
                haju.topleft = (haju.topleft[0]-1,haju.topleft[1])
                #pygame.draw.rect(window,(120,0,0),haju,3)

class Note(Object):
    """Object that sounds a designated pitch following collision with Player"""
    def __init__(self,tone,grid):
        space = grid.mapping[0][0]
        noteSrf = pygame.surface.Surface((space.height,space.width))
        noteSrf.fill((200,100,100))
        pygame.draw.rect(noteSrf,(100,200,100),noteSrf.get_rect(),3)
        Object.__init__(self,img=noteSrf,rect=grid.mapping[len(grid.mapping)-1]
                        [chromatic.index(tone)]) # assign vertical position by tone

# Music Control Objects -------------------------------------------------------------

class Scales:
    """Class for scale structures (not game object)"""
    def __init__(self,tonic,mode):
        self.scale = Scales.genScale(tonic,mode)
        self.tonic = self.scale[0]
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
        """Return all scales (that are dealt with by this program)"""
        MegaScale = [] # v (below) a global list should be made for these
        for a in ['maj','nmin','hmin','jmin']: # for each scale mode
            for b in chromatic: # for each note in the chromatic scale
                MegaScale.append(Scales.genScale(b,a)) # add scale b in mode a
        return tuple(MegaScale)

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

# Data Constants --------------------------------------------------------------------

chromatic = ('c','c#','d','d#','e','f',
             'f#','g','g#','a','a#','b')
modes = {'maj': (2,2,1,2,2,2,1),'nmin': (2,1,2,2,1,2,2),
         'hmin': (2,1,2,2,1,3,1),'jmin': (2,1,2,2,2,2,1)}
scales = Scales.getAllScales()

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
flimmy = Player()
raga = Grid()
stimpy = Note(tone='f',grid=raga)

def gameloop():
    for event in pygame.event.get():
        print event
        if event.type == QUIT:
            pygame.quit()
            #sys.exit()
            break

    for a in drawObjects.sprites():
        a.clean() # clear sprites
    raga.move() # move grid
    activeObjects.update() # update active objects
    drawObjects.draw(window) # draw sprites

    pygame.display.update()
    clock.tick(60)
    
while True:
    gameloop()
