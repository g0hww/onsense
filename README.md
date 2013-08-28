OnSense
=======

OnSense is a hacktastic hybrid spectrum sensing scanner using a combination of SDR and conventional receivers.  It is currently a simple wrapper for osmocom_spectrum_sense primarily supporting the HackRF Jawbreaker (but other devices supported by the osmosdr front end should work to some degree) and uses hamlib's rigctl (optionally via rigctld) to tune a communications receiver.

I've been using OnSense with a HackRF Jawbreaker and an AOR-8600mk2 receiver.  OnSense is capable of scanning the entire military UHF band in less than a second using the HackRF device and commands the AOR receiver to tune to the strongest detected signal.  There is a mechanism lurking in the code that pretends to be an algorithm which tries to avoid attention defecit disorder in the receiver. It can only be improved upon.

The file "onsense.py" contains the application script.  The "onsense" file is a simple bash script taking one of two alternate options, "civair" or "milair".  The bash script contains configuration options for onsense.py that I've used here with success.  You may need to edit some or most of the options yourself, for some reason or another, mostly likely to try and avoid osmocom_spectrum_sense crashing so often, which OnSense conventiently handles fairly well.  If osmocom_spectrum_sense seems to be crashier than usual simply disconnecting and reconnecting the HackRF device works for me.

More words will follow imminently, and probably more code.  I'm trying to get my head around QT in order to give this a GUI and more features.  A database is likely to put in an appearance in the near future too.

Oh yeah.  I almost forgot.  There's a hardcoded blacklist in "onsense.py".  You either want to delete it or modify it, or both. Also, try and avoid receiving a mess of intermod. It will result in frustration and probably a headache.

Onsense spits out a bunch of characters  as well as detection reports and perhaps desktop notifications as it eats output from osmocom_spectrum_sense. The characters emmitted on stdout are probably:

        'c' ... a detection report was for a dwell centre frequency, and was surpressed by the mechanism for reducing detections of the 0Hz
        centre from each dwell.  The -c option controls the margin used for centre suppression.
        
        'x' ... a blacklisted frequency was supressed. The blacklist is currently in "onsense.py"
        
        '-' ... the power threshold for slave receiver tuning was reduced as some weaker signals are there to be listened to
        
        '=' ... the power threshold for slave receiver tuning is the squelch threshold
        
        '.' ... nothing was received.  currently we expect to receive detection reports for each dwell with the HackRF. Not seeing anything is a convenient way to 			tell that osmocom_spectrum_sense has barfed.  In future I shall ship a fork of the osmocom script that tags dwell limits and removes the need to
        make use of observations of the DC cruft in order to avoid timeouts.  This would be needed if we wanted to use a UHD device with offset tuning. If you see a 			'.' expect a restart of the osmocom process.
  
 I use rigctld to control the conventional receiver.  I keep grig running at the same time so I don't have to stare at the receiver to figure out what is going on.
 
 Happy listening :)




