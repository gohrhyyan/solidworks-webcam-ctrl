A lightweight, webcam-powered Python script that enables enables engineers to manipulate 3D models using natural gestures via their laptop's front-facing webcam.

By leveraging MediaPipe's real-time hand tracking and the pySW library (a Python wrapper for the SolidWorks COM API). The MVP focuses on core viewport navigation—orbits, pans, and zooms—without the need for a compiled .NET add-in or inter-process communication. Everything runs in a single Python process for minimal latency and easy setup.

User Interaction Flow
The system processes your webcam feed. MediaPipe detects up to two hands, extracting 21 landmarks per hand for precise tracking. Gestures trigger only on a "pinch" (thumb-to-index distance < 5% of hand width, tunable via config file). Hand translations map directly to viewport commands in real-time, based on pixel deltas per frame (scaled by a sensitivity slider in settings). win32COM dispatches these to SolidWorks' IModelView interface for seamles. Exit any gesture by releasing the pinch; the system resets to idle.

Single-Hand Rotation (Orbit)
Activation: Raise one hand into frame and close thumb-to-index for a steady pinch.
Manipulation: Translate your pinched hand left/right/up/down across the screen. The model orbits fluidly around its center: horizontal swipes induce yaw (rotate side-to-side), vertical ones pitch (up/down tilt). Speed scales with hand velocity (e.g., slow drag for fine tweaks, quick flick for broad spins). Diagonal moves decompose into combined yaw/pitch via vector math. Under the hood: 

Dual-Hand Translation (Pan)
Activation: When two hands are detected and both perform a pinch gesture, enter translate mode.
Translation (Parallel Move): Keep hands pinched at consistent width and move them together in unison—horizontal/vertical/diagonal drags pan the entire viewport (model slides without rotating). Ideal for recentering on a sub-assembly. 
Adjusts based on average hand speed for smooth tracking. 

WIP
Zoom (Scale)
Zoom (Spread/Contract): While two hands are pinched, vary hand width—spread apart to zoom in (enlarges details), contract together to zoom out (model shrinks, revealing context). Width change rate dictates speed: slow spread for gradual reveal, fast for quick overviews. 