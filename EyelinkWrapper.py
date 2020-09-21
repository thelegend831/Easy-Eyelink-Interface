# -*- coding: utf-8 -*-
"""
A custom module to make interaction with the eyelink 1000+ more
straightforward. Depends on the **pylink** module that ships with SR-Research's
'Developer Pack'. After installation, you will have folder containing this
module somewhere on your computer. Make sure to copy it to the
``site-packages`` folder of your python distribution.
Official Python repositories include another module called *pylink*, which is
absolutely unrelated. So ``pip`` or ``conda install`` won't work!

**Author** :
    Wanja Mössing, WWU Münster | moessing@wwu.de
**Version**:
    July 2017
**copyright** :
  Copyright (C) 2016 Wanja Mössing

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

# import dependencies to global
import pylink
from os import path, getcwd, mkdir
from numpy import sqrt as np_sqrt, sum as np_sum, array as np_array
from EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy
# SR-Research's EyeLinkCoreGraphicsPsychoPy can be retrieved here:
# https://www.sr-support.com/forum/eyelink/programming/5548-a-psychopy-implementation-of-the-eyelink-coregraphics


def notify(message='( ^_^)/ XX-XX ＼(^_^ )', el=pylink.getEYELINK()):
    """ Prints a message on Eyelink host-pc's interface
    **Author** : Wanja Mössing, WWU Münster | moessing@wwu.de \n
    *June 2018*

    Parameters:
    ----------
    message : string
    message to be shown
    el     :
        Eyelink object, optional
    """
    msg = "record_status_message \'"
    msg += message
    msg += "\'"
    el.sendCommand(msg)


def AvoidWrongTriggers():
    """ Throws an error if Eyelink is connected but not configured.\n
    *Only needed in EEG experiments without Eyetracking!*

    **Author** : Wanja Mössing, WWU Münster | moessing@wwu.de \n
    *July 2017*

    Since we use a Y-cable which is supposed to send the TTL-triggers from
    the Python-PC to EEG & Eyetracker host, there is a permanent
    connection between the three parallelports (1. EEG, 2.Python, 3.Eyelink).
    Therefore, all parallelports need to be set low, except for the one
    putting the triggers (i.e. Python). The Eyelink host-pc sends a random
    trigger at startup if not configured properly. So if an experiment that
    doesn't use the Eyetracker sends a trigger to the EEG while the
    Eyetracker host-pc is turned on, that causes a wrong trigger in the EEG
    signal. This function can be placed at the beginning of an
    experiment that doesn't use the eyelink to throw an error if the eyelink
    is still connected.
    """
    from os import system as sys
    from platform import system as sys_name
    print 'Pinging Eyelink to check if connected and powered...'

    if sys_name() == 'Windows':
        r = sys('ping -n 1 100.1.1.1')
    else:
        r = sys('ping -c 1 100.1.1.1')

    if r != 0:
        msg = """Eyelink host PC is turned on. Without running the appropriate
        startup routines (e.g., `EyelinkStart` from Wanja`s Github repo),
        this will cause faulty triggervalues in your EEG signal, because the
        parallel-port of the Eyelink-PC is set to a random value at startup
        instead of reading the port. Either turn off the Eyelink-PC or
        configure it!"""
        print(msg)
        raise SystemExit
    return


def EyelinkCalibrate(targetloc=(1920, 1080),
                     el=pylink.getEYELINK()):
    """ Performs calibration for Eyelink 1000+.

    **Author** : Wanja Mössing, WWU Münster | moessing@wwu.de \n
    *July 2017*

    Parameters:
    ----------
    target : tuple
        two-item tuple width & height in px
    el     :
        Eyelink object, optional
    """
    el.sendMessage("STOP_REC_4_RECAL")
    # wait 100ms to catch final events
    pylink.msecDelay(100)
    # stop the recording
    el.stopRecording()
    # do the calibration
    el.doTrackerSetup(targetloc[0], targetloc[1])
    # clear tracker display and draw box at center
    el.sendCommand("clear_screen 0")
    el.sendCommand("set_idle_mode")
    pylink.msecDelay(50)
    # re-start recording
    el.startRecording(1, 1, 1, 1)
    return el


def EyelinkDriftCheck(targetloc=(1920, 1080),
                      el=pylink.getEYELINK()):
    """ Performs Driftcheck for Eyelink 1000+.

    **Author** : Wanja Mössing, WWU Münster | moessing@wwu.de \n
    *July 2017*

    Parameters:
    ----------
    target : tuple
        two-item tuple width & height in px
    el       :
        Eyelink object, optional
    """
    # drift check
    try:
        el.sendMessage("STOP_REC_4_DRIFTCHECK")
        # wait 100ms to catch final events
        pylink.msecDelay(100)
        # stop the recording
        el.stopRecording()
        res = el.doDriftCorrect(targetloc[0], targetloc[1], 1, 1)
        # clear tracker display and draw box at center
        el.sendCommand("clear_screen 0")
        el.sendCommand("set_idle_mode")
        pylink.msecDelay(50)
        # re-start recording
        el.startRecording(1, 1, 1, 1)
    except:
        res = EyelinkCalibrate(targetloc, el)
    return res


def EyelinkStart(dispsize, Name, win, bits=32, dummy=False,
                 colors=((0, 0, 0), (192, 192, 192))):
    """ Performs startup routines for the EyeLink 1000 Plus eyetracker.

    **Author** : Wanja Mössing, WWU Münster | moessing@wwu.de \n
    *July 2017*

    Parameters:
    -----------
    dispsize : tuple
        two-item tuple width & height in px
    Name    : string
        filename for the edf. Doesn't have to, but can, end on '.edf'
        Maximum length is 8 (without '.edf').
        Possible alphanumeric input: 'a-z', 'A-Z', '0-9', '-' & '_'
    win     : window object
        You necessarily need to open a psychopy window first!
    bits    : integer
        color-depth, defaults to 32
    dummy   : boolean
        Run tracker in dummy mode?
    colors  : Tuple, Optional.
        Tuple with two RGB triplets

    Returns
    -------
    'el' the tracker object.
             This can be passed to other functions,
             although they can use pylink.getEYELINK()
             to find it automatically.
    """
    print('. ')
    # get filename
    if '.edf' not in Name.lower():
        if len(Name) > 8:
            print('EDF filename too long! (1-8 characters/letters)')
            raise SystemExit
        else:
            Name += '.edf'
    elif '.edf' in Name.lower():
        if len(Name) > 12:
            print('EDF filename too long! (1-8 characters/letters)')
            raise SystemExit
    print('. ')
    # initialize tracker object
    if dummy:
        el = pylink.EyeLink(None)
    else:
        el = pylink.EyeLink("100.1.1.1")
    print('. ')
    # Open EDF file on host
    el.openDataFile(Name)
    print('. ')
    # set file preamble
    currentdir = path.basename(getcwd())
    FilePreamble = "add_file_preamble_text \'"
    FilePreamble += "Eyetracking Dataset AE Busch WWU Muenster Experiment: "
    FilePreamble += currentdir + "\'"
    el.sendCommand(FilePreamble)
    print('. ')
    # this function calls the custom calibration routine
    # "EyeLinkCoreGraphicsPsychopy.py"
    genv = EyeLinkCoreGraphicsPsychoPy(el, win)
    pylink.openGraphicsEx(genv)
    print('. ')
    # set tracker offline to change configuration
    el.setOfflineMode()
    print('. ')
    # flush old keys
    pylink.flushGetkeyQueue()
    print('. ')
    # set sampling rate
    el.sendCommand('sample_rate 1000')
    print('. ')
    # Sets the display coordinate system and sends mesage to that
    # effect to EDF file;
    el.sendCommand("screen_pixel_coords =  0 0 %d %d" %
                   (dispsize[0] - 1, dispsize[1] - 1))
    el.sendMessage("DISPLAY_COORDS  0 0 %d %d" %
                   (dispsize[0] - 1, dispsize[1] - 1))
    print('. ')
    # select parser configuration for online saccade etc detection
    ELversion = el.getTrackerVersion()
    ELsoftVer = 0
    if ELversion == 3:
        tmp = el.getTrackerVersionString()
        tmpidx = tmp.find('EYELINK CL')
        ELsoftVer = int(float(tmp[(tmpidx + len("EYELINK CL")):].strip()))
    if ELversion >= 2:
        el.sendCommand("select_parser_configuration 0")
    if ELversion == 2:
        # turn off scenelink stuff (that's an EL2 front-cam addon...)
        el.sendCommand("scene_camera_gazemap = NO")
    else:
        el.sendCommand("saccade_velocity_threshold = 35")
        el.sendCommand("saccade_acceleration_threshold = 9500")
    print('. ')
    # set EDF file contents AREA
    el.sendCommand("file_event_filter = LEFT,RIGHT,FIXATION,"
                   "SACCADE,BLINK,MESSAGE,BUTTON,INPUT")
    if ELsoftVer >= 4:
        el.sendCommand("file_sample_data = LEFT,RIGHT,GAZE,HREF,"
                       "AREA,HTARGET,GAZERES,STATUS,INPUT")
    else:
        el.sendCommand("file_sample_data = LEFT,RIGHT,GAZE,HREF,"
                       "AREA,GAZERES,STATUS,INPUT")
    print('. ')
    # set link data (online interaction)AREA
    el.sendCommand("link_event_filter = LEFT,RIGHT,FIXATION,SACCADE,"
                   "BLINK,MESSAGE,BUTTON,INPUT")
    if ELsoftVer >= 4:
        el.sendCommand("link_sample_data = LEFT,RIGHT,GAZE,GAZERES,AREA,"
                       "HTARGET,STATUS,INPUT")
    else:
        el.sendCommand("link_sample_data = LEFT,RIGHT,GAZE,GAZERES,AREA,"
                       "STATUS,INPUT")
    print('. ')
    # run initial calibration
    # 13-Pt Grid calibration
    el.sendCommand('calibration_type = HV13')
    el.doTrackerSetup(dispsize[0], dispsize[1])
    # put tracker in idle mode and wait 50ms, then really start it.
    el.sendMessage('SETUP_FINISHED')
    el.setOfflineMode()
    pylink.msecDelay(500)
    # set to realtime mode
    pylink.beginRealTimeMode(200)
    # start recording
    # note: sending everything over the link *potentially* causes buffer
    # overflow. However, with modern PCs and EL1000+ this shouldn't be a real
    # problem
    el.startRecording(1, 1, 1, 1)

    # to activate parallel port readout without modifying the FINAL.INI on the
    # eyelink host pc, uncomment these lines
    # tyical settings for straight-through TTL cable (data pins -> data pins)
    el.sendCommand('write_ioport 0xA 0x20')
    el.sendCommand('create_button 1 8 0x01 0')
    el.sendCommand('create_button 2 8 0x02 0')
    el.sendCommand('create_button 3 8 0x04 0')
    el.sendCommand('create_button 4 8 0x08 0')
    el.sendCommand('create_button 5 8 0x10 0')
    el.sendCommand('create_button 6 8 0x20 0')
    el.sendCommand('create_button 7 8 0x40 0')
    el.sendCommand('create_button 8 8 0x80 0')
    el.sendCommand('input_data_ports  = 8')
    el.sendCommand('input_data_masks = 0xFF')
    # tyical settings for crossover TTL cable (data pins -> status pins)
#    el.sendCommand('write_ioport 0xA 0x0')
#    el.sendCommand('create_button 1 9 0x20 1')
#    el.sendCommand('create_button 2 9 0x40 1')
#    el.sendCommand('create_button 3 9 0x08 1')
#    el.sendCommand('create_button 4 9 0x10 1')
#    el.sendCommand('create_button 5 9 0x80 0')
#    el.sendCommand('input_data_ports  = 9')
#    el.sendCommand('input_data_masks = 0xFF')
    # mark end of Eyelinkstart in .edf
    el.sendMessage('>EndOfEyeLinkStart')
    # return Eyelink object
    return el


def EyelinkStop(Name, el=pylink.getEYELINK()):
    """ Performs stopping routines for the EyeLink 1000 Plus eyetracker.

    **Author** : Wanja Mössing, WWU Münster | moessing@wwu.de \n
    *July 2017*

    Parameters:
    -----------
    Name    : string
        filename of the edf. Doesn't have to, but can, end on '.edf'
        Must be the same name used during EyelinkStart()
    el : Eyelink Object
        Eyelink object returned by EyelinkStart().
        By default this function tried to find it itself.
    """
    # Check filename
    if '.edf' not in Name.lower():
            Name += '.edf'
    # stop realtime mode
    pylink.endRealTimeMode()
    # make sure all experimental procedures finished
    pylink.msecDelay(1000)
    # stop the recording
    el.stopRecording()
    # put Eyelink back to idle
    el.setOfflineMode()
    # wait for stuff to finish
    pylink.msecDelay(500)
    # close edf
    el.closeDataFile()
    # transfer edf to display-computer
    try:
        print('Wait for EDF to be copied over LAN...')
        if not path.exists('./EDF'):
            mkdir('./EDF')
        el.receiveDataFile(Name, './EDF/'+Name)
        print('Done. EDF has been copied to ./EDF folder.')
    except RuntimeError:
        print('Error while pulling EDF file. Try to find it on Eyelink host..')
    el.close()
    pylink.closeGraphics()
    return


def EyelinkGetGaze(targetLoc, FixLen, dispsize, el=pylink.getEYELINK(),
                   isET=True, PixPerDeg=None, IgnoreBlinks=False,
                   OversamplingBehavior=None):
    """ Online gaze position output and gaze control for Eyelink 1000+.

    **Author** : Wanja Mössing, WWU Münster | moessing@wwu.de \n
    *July 2017*

    Parameters
    ----------
    targetLoc : tuple
        two-item tuple x & y coordinates in px; defines where subject should
        look at ([0, 0] is center - just as psychopy assumes it.)
    FixLen : int
        A circle around a specified point is set as area that subjects are
        allowed to look at. ``FixLen`` defines the radius of that circle.
        Can be in degree or pixels. If ``PixPerDeg`` is not empty, assumes
        degree, else pixels.
    el: Eyelink object
        ...as returned by, e.g., ``EyelinkStart()``. You can try to run it
        without passing ``el``. In that case ``EyelinkGetGaze()`` will try to
        find ``el``.
    dispsize : tuple
        Needed because PP thinks (0,0)=center, but EL thinks (0,0)= topleft
    isET: boolean, default=True
        Is Eyetracker connected? If ``False``, returns display center as
        coordinates and ``hsmvd=False``.
    PixPerDeg: float
        How many pixels per one degree of visual angle? If provided, ``FixLen``
        is assumed to be in degree.
    IgnoreBlinks: boolean, default=False
        If True, missing gaze position is replaced by center coordinates.
    OversamplingBehavior: None
        Defines what is returned if nothing new is available.

    Returns
    -------
    GazeInfo: dict
        Dict with elements ``x``,``y``, and ``hsmvd``. ``x`` & ``y`` are gaze
        coordinates in pixels. ``hsmvd`` is boolean and defines whether gaze
        left the circle set with FixLen.
    """
    # IF EYETRACKER IS CONNECTED...
    if isET:
        # This is just for clarity
        RIGHT_EYE = 1
        LEFT_EYE = 0
        BINOCULAR = 2

        # ---------- deprecated but maybe useful later...----------------------
        # check if new data available via link
        # eventType = el.getNextData()
        # if it's a saccade or fixation, get newest gaze data available
        # if eventType in {pylink.STARTFIX, pylink.FIXUPDATE, pylink.ENDFIX,
        #                 pylink.STARTSACC, pylink.ENDSACC}:
        # if it's a blink, adjust output accordingly
        # elif eventType in {pylink.STARTBLINK,pylink.ENDBLINK}:
        # ---------------------------------------------------------------------

        # Get the newest data sample
        sample = el.getNewestSample()
        # get the newest event
        event = el.getNextData()
        # returns none, if no new sample available
        if sample is not None:
            # check which eye has been tracked and retrieve data for this eye
            if el.eyeAvailable() is LEFT_EYE and sample.isLeftSample():
                # getGaze() return Two-item tuple in the format of
                # (float, float). -> (x,y) in px
                # getPupilSize return float in arbitrary units. The meaning of
                # this depends on the settings made (area or diameter)
                gaze = sample.getLeftEye().getGaze()
                pupil = sample.getLeftEye().getPupilSize()
            elif el.eyeAvailable() is RIGHT_EYE and sample.isRightSample():
                gaze = sample.getRightEye().getGaze()
                pupil = sample.getRightEye().getPupilSize()
            elif el.eyeAvailable() is BINOCULAR:
                print 'Binocular mode not yet implemented'
                return None
            else:
                raise Exception('Could not detect which eye has been tracked')

            # Check if subject blinks or if data are just randomly missing
            if pylink.MISSING_DATA in gaze:
                # check how sure we are whether it is a blink
                if event is pylink.STARTBLINK:
                    print('Subject is definitely blinking')  # debugging
                    blinked = True
                elif pupil == 0:
                    print('Subject is probably blinking')  # debugging
                    blinked = True
                else:
                    print('Missing data but no blink?')  # debugging
                    blinked = False
                # assign values accordingly
                if blinked and not IgnoreBlinks:
                    hsmvd = True
                elif blinked and IgnoreBlinks:
                    hsmvd = False
                    gaze = targetLoc
                elif not blinked:
                    hsmvd = True
            else:
                # Eyelink thinks (0,0) = topleft, PsyPy thinks it's center...
                xhalf = dispsize[0]/2
                yhalf = dispsize[1]/2
                x = gaze[0]
                y = gaze[1]
                if x >= xhalf:
                    xout = x - xhalf
                else:
                    xout = (xhalf - x) * -1
                if y >= yhalf:
                    yout = (y - yhalf) * -1
                else:
                    yout = yhalf - y
                gaze = (xout, yout)
                # transform location data to numpy arrays, so we can calculate
                # euclidean distance
                a = np_array(targetLoc)
                b = np_array(gaze)
                # get euclidean distance in px
                dist = np_sqrt(np_sum((a-b)**2))
                # check if we know how many px form one degree.
                # If we do, convert to degree
                if PixPerDeg is not None:
                    dist = dist/PixPerDeg
                # Now check whether gaze is in allowed frame
                hsmvd = dist > FixLen

            # return dict
            return {'x': gaze[0], 'y': gaze[1], 'hsmvd': hsmvd,
                    'pupilSize': pupil}
        # If no new sample is available return None
        elif sample is None:
            return OversamplingBehavior
    # IF EYETRACKER NOT CONNECTED RETURN TARGETLOCATION AND NO PUPIL SIZE
    elif not isET:
        return {'x': targetLoc[0], 'y': targetLoc[1], 'hsmvd': False,
                'pupilSize': None}


def EyelinkSendTabMsg(infolist, el=pylink.getEYELINK()):
    """ Sends tab-delimited message to EDF

    **Author** : Wanja Mössing, WWU Münster | moessing@wwu.de \n
    *July 2017*

    Parameters
    ----------
    infolist : list
        a list with information. The first item in the list is used as
        event-definition (e.g., ['trialOnset', 1, 'Condition X', 0.78])
        Can take strings, integers, floats
    el: Eyelink object
        ...as returned by, e.g., EyelinkStart()
    """
    # if it's not a list convert
    if not isinstance(infolist, list):
        infolist = [infolist]
    # prepend identifier if necessary
    if infolist[0] is not '>':
        infolist.insert(0, '>')
    # make it a tab delimited list and convert everything to string
    msg = '\t'.join(str(i) for i in infolist)
    # send to Eyetracker
    el.sendMessage(msg)
    return
