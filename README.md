OnSense
=======

OnSense is a hybrid spectrum sensing scanner using a combination of SDR and conventional receivers.  It is currently a simple wrapper for osmocom_spectrum_sense.

I've been using OnSense with a HackRF Jawbreaker and an AOR-8600mk2 receiver.  On my fast computer, OnSense is capable of scanning the entire military UHF band in less than a second using the HackRF device and commands the AOR receiver to tune to the strongest detected signal.  There is a mechanism lurking in the code that pretends to be an algorithm which tries to avoid attention defecit disorder in the receiver. It can only be improved upon.

The file "onsense.py" contains the application script.  The "onsense" is a simple bash script taking one of two alternate options, "civair" or "milair".  The bash script contains configuration options for onsense.py that I've used here with success.  You may need to edit some or most of the options yourself, for some reason or another, mostly likely to try and avoid osmocom_spectrum_sense crashing so often, which OnSense conventiently handles fairly well.  If osmocom_spectrum_sense seems to be crashier than usual simply disconnecting and reconnecting the HackRF device works for me.

More words will follow imminently, and probably more code.  I'm trying to get my head around QT in order to give this a GUI and more features.  A database is likely to put in an appearance in the near future too.

Oh yeah.  I almost forgot.  There's a hardcoded blacklist in "onsense.py".  You either want to delete it or modify, or both.


