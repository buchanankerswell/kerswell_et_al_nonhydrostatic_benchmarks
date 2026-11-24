# Key results

The sink suite holds 25 registered runs (`project.mk`, S1-S24 plus the CFL1.0
twin). S1 is the undamped full-feedback run; S2 turns the feedback off. Both
sit at Res6, CFL 0.5, kinetic prefactor Z = 4.44e-04 1/s/K. Every number below
comes from `simulation/results/*.csv`.

## What the suite shows

The oscillation is a feedback artifact. S1 reaches a domain-wide dynamic
pressure range of 2168 MPa at 1.75 Ma and a peak grid-band (<20 km) lateral
amplitude of 157 MPa. S2 reaches 386 MPa and 0.4 MPa. S1 overshoots the
no-feedback reference by 462%. At the peak step its lateral profile runs from
-707 to +594 MPa; S2 stays within -154 to +18 MPa.

Bulk viscosity does not damp it. Implicit bulk viscosity of 1e18-1e20 Pa s and
explicit bulk viscosity of 1e19 Pa s leave the peak grid band at 165-225 MPa,
worse than S1. Explicit 1e20 Pa s crashes at step 1. Every complete bulk run
has zero or negative reduction against the undamped control.

Relaxed pressure works. A relaxation time tau of 1-100 kyr
(3.156e10-3.156e12 s) cuts the peak grid band to 0.3-7 MPa and the largest
pressure range to 408-426 MPa, about 80% below S1. Tau of 100 yr cuts 40%;
tau of 10 yr still rings at 133 MPa. Suppression holds at Res7 and CFL0.25,
where the undamped base case crashes.

The pressure cap works but drifts with resolution. At Res6, Cap1e8 (100 MPa)
gives the smallest range (354 MPa, 84% reduction), Cap2e8 gives 555 MPa, and
Cap4e8 gives 1229 MPa. The same Cap2e8 gives 350, 555, and 905 MPa at Res5,
Res6, and Res7; its grid band grows from 4 to 48 to 139 MPa.

Finer mesh and smaller time step make the undamped case worse. Res5 barely
rings (grid 2 MPa, range 350 MPa), Res6 rings hard (2168 MPa), and Res7
crashes at step 0. CFL1.0 completes clean at 344 MPa while CFL0.25 crashes.
The undamped solution does not converge under refinement; the relaxed Res7 run
does.

Damping barely moves the final 410. At Res6 the final 410 displacement stays
near 2.8-2.9 km and the front width near 3.5-3.8 km across almost every
damper. The thermal part of the displacement is ~0 km, so kinetics carry all
of it. The 100 kyr relaxed run sits at 3.1 km and the relaxed Res7 run at
3.6 km. Cap2e8 at Res7 ends at 37 /Ma, against 2.3 /Ma at Res6.

Two new figures make the timescales and the trade-off visible.
`timescales-sink.png` places the phase-change time (419 kyr), flow and pressure
relaxation (3.14 and 2.75 Ma), the oscillation peak (1.75 Ma), output cadence
(250 kyr), solver cap (25 kyr), and tau window (10 yr-100 kyr) on one log axis.
Tau is shorter than the reaction time and far shorter than viscous relaxation.
`relaxed-mean-check-sink.png` shows the compromise: every relaxed run settles
near -135 MPa lateral mean, against -37 MPa for S2 and -57 MPa for S1. That
~100 MPa offset appears in all seven relaxed variants and in no bulk or cap
run. A linear filter cannot create it by lag.

## What is still missing

1. Explain the -100 MPa relaxed mean. Write the relaxation field at each step
   and compare its mean with the Stokes pressure; decide whether it is a
   physical load or a field bias before calling relaxed pressure a physical
   fix.
2. Decide the five crashed runs (Bexpl1e20, Bimpl1e19 CFL0.25, Bimpl1e19
   Res7, undamped Res7, undamped CFL0.25). Resubmit or drop them from the
   suite so the figure set is complete.
3. Add no-feedback reference runs at Res5, Res7, CFL0.25, and CFL1.0. Only
   Res6 has one today, so `displacement-error-sink.png` borrows the Res6 value
   for Res5 and Res7 points and relative error is undefined across the sweep.
4. Repeat the Cap2e8 Res7 case. Its 37 /Ma final rate may be an unsettled front
   rather than a sharp one.
5. Re-render the remaining depth-window and mesh panels at fixed display limits
   and `FIG_DPI=330`.
6. Measure 520 and 660. Postprocessing scores the 410 (olivine-wadsleyite)
   front only, yet the paper asks about all three discontinuities.
7. Add a community reference case (see `benchmark-design.md`) so the feedback
   is not tied to our sinking-block setup.
