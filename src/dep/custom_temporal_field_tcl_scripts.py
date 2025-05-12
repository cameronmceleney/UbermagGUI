def drive_pause_drive():
    tcl_strings = {'script': "proc TimeFunction:{drive_name}"}
    tcl_strings['script'] += ' '

    tcl_strings["script"] = """
    { total_time } {
      set PI [expr {4 * atan(1.0)}]
      set w [expr {2 * $PI * 20e9}]
      set tt [expr {$total_time - 0}]
      set wt [expr { $w * $tt }]
      set f [expr { sin($wt) }]
      set df [expr { $w * cos($wt) }]
      set ft [expr { $f }]
      set dft [expr { $df }]
      if {$total_time < 4e-9} {
    
        return [list $ft   0    0 \
                       0 $ft    0 \
                       0   0  $ft \
                     $dft  0    0 \
                       0  $dft  0 \
                       0   0  $dft]
        } elseif {$total_time < 12e-9} {
          return [list 0 0 0 \
                       0 0 0 \
                       0 0 0 \
                       0 0 0 \
                       0 0 0 \
                       0 0 0]
        } else {
          return [list $ft   0    0 \
                         0 $ft    0 \
                         0   0  $ft \
                       $dft  0    0 \
                         0  $dft  0 \
                         0   0  $dft]
        }
    }
    """
    tcl_strings["energy"] = "Oxs_TransformZeeman"
    tcl_strings["type"] = "general"
    tcl_strings["script_args"] = "total_time"
    tcl_strings["script_name"] = f"TimeFunction:{drive_name}"

    return tcl_strings


def drive_pause_drive_rotate_90degrees(drive_name: str = 'drive'):
    tcl_strings = {'script': "proc TimeFunction:{drive_name}"}
    tcl_strings['script'] += ' '

    tcl_strings["script"] = """
    { total_time } {
        # Define constants and angular frequency: ω = 2π * (20e9)
        set PI [expr {4.0 * atan(1.0)}]
        set w [expr {2.0 * $PI * 20e9}]
        # Use t directly (with no offset) to compute the phase:
        set phi [expr {$w * $total_time}]
    #
        if {$total_time < 4e-9} {
            # Interval 1: Driving field in the x-y plane.
            # Use rotation matrix R_z(phi) but force no z-component:
            # T = [ cos(phi)    -sin(phi)   0.0 ;
            #       sin(phi)     cos(phi)   0.0 ;
            #       0.0          0.0        0.0 ]
            # dT/dt = [ -w*sin(phi)    -w*cos(phi)   0.0 ;
            #           w*cos(phi)     -w*sin(phi)   0.0 ;
            #           0.0            0.0          0.0 ]
            return [list \
                [expr {cos($phi)}] [expr {-1.0 * sin($phi)}] 0.0 \
                [expr {sin($phi)}] [expr {cos($phi)}] 0.0 \
                0.0 0.0 0.0 \
                [expr {-1.0 * $w * sin($phi)}] [expr {-1.0 * $w * cos($phi)}] 0.0 \
                [expr {$w * cos($phi)}] [expr {-1.0 * $w * sin($phi)}] 0.0 \
                0.0 0.0 0.0]
        } elseif {$total_time < 12e-9} {
            # Interval 2: No driving field (all matrix elements zero).
            return [list 0.0 0.0 0.0 \
                          0.0 0.0 0.0 \
                          0.0 0.0 0.0 \
                          0.0 0.0 0.0 \
                          0.0 0.0 0.0 \
                          0.0 0.0 0.0]
        } else {
            # Interval 3: Driving field in the x-y plane rotated by 90°.
            # A 90° phase shift means use phi_new = phi + (pi/2).
            # Using the identities:
            #   cos(phi+pi/2) = - sin(phi)
            #   sin(phi+pi/2) = cos(phi)
            # the transformation matrix becomes:
            # T = [ -sin(phi)   -cos(phi)   0.0 ;
            #       cos(phi)    -sin(phi)   0.0 ;
            #       0.0         0.0        0.0 ]
            # and its derivative is:
            # dT/dt = [ -w*cos(phi)    w*sin(phi)   0.0 ;
            #           -w*sin(phi)   -w*cos(phi)   0.0 ;
            #            0.0          0.0          0.0 ]
            return [list \
                [expr {-1.0 * sin($phi)}] [expr {-1.0 * cos($phi)}] 0.0 \
                [expr {cos($phi)}] [expr {-1.0 * sin($phi)}] 0.0 \
                0.0 0.0 0.0 \
                [expr {-1.0 * $w * cos($phi)}] [expr {$w * sin($phi)}] 0.0 \
                [expr {-1.0 * $w * sin($phi)}] [expr {-1.0 * $w * cos($phi)}] 0.0 \
                0.0 0.0 0.0]
        }
    }
    """
    tcl_strings["energy"] = "Oxs_TransformZeeman"
    tcl_strings["type"] = "general"
    tcl_strings["script_args"] = "total_time"
    tcl_strings["script_name"] = f"TimeFunction:{drive_name}"

    return tcl_strings


def drive_pause_drive_rotate_counterclockwise(drive_name: str = 'drive'):
    tcl_strings = {'script': "proc TimeFunction:{drive_name}"}
    tcl_strings['script'] += ' '

    tcl_strings['script'] += """
    { total_time } {
        # Define PI and angular frequency: ω = 2π·20e9
        set PI [expr {4.0 * atan(1.0)}]
        set w [expr {2.0 * $PI * 20e9}]
        # Compute phase φ = ω·total_time
        set phi [expr {$w * $total_time}]

        if {$total_time < 4e-9} {
            # Interval 1: Clockwise rotation.
            # Use R_z(-φ):
            #   T = [ cos(φ)   sin(φ)   0.0 ;
            #         -sin(φ)  cos(φ)   0.0 ;
            #          0.0     0.0      1.0 ]
            set T11 [expr {cos($phi)}]
            set T12 [expr {sin($phi)}]
            set T13 0.0
            set T21 [expr {-1.0 * sin($phi)}]
            set T22 [expr {cos($phi)}]
            set T23 0.0
            set T31 0.0
            set T32 0.0
            set T33 1.0
            # Time derivative of R_z(-φ):
            #   dT/dt = [ -ω·sin(φ)   ω·cos(φ)   0.0 ;
            #             -ω·cos(φ)  -ω·sin(φ)   0.0 ;
            #              0.0       0.0        0.0 ]
            set dT11 [expr {-1.0 * $w * sin($phi)}]
            set dT12 [expr {$w * cos($phi)}]
            set dT13 0.0
            set dT21 [expr {-1.0 * $w * cos($phi)}]
            set dT22 [expr {-1.0 * $w * sin($phi)}]
            set dT23 0.0
            set dT31 0.0
            set dT32 0.0
            set dT33 0.0
            return [list $T11 $T12 $T13 \
                         $T21 $T22 $T23 \
                         $T31 $T32 $T33 \
                         $dT11 $dT12 $dT13 \
                         $dT21 $dT22 $dT23 \
                         $dT31 $dT32 $dT33]
        } elseif {$total_time < 12e-9} {
            # Interval 2: No drive; return a 3x3 zero matrix and zero derivative.
            return [list 0.0 0.0 0.0  0.0 0.0 0.0  0.0 0.0 0.0  \
                         0.0 0.0 0.0  0.0 0.0 0.0  0.0 0.0 0.0]
        } else {
            # Interval 3: Polarised drive in the xy plane, rotated 90° with counterclockwise rotation.
            # Define ψ = φ + π/2:
            set psi [expr {$phi + (0.5 * $PI)}]
            # Use R_z(ψ):
            #   T = [ cos(ψ)   -sin(ψ)   0.0 ;
            #         sin(ψ)    cos(ψ)   0.0 ;
            #         0.0       0.0      1.0 ]
            set T11 [expr {cos($psi)}]
            set T12 [expr {-1.0 * sin($psi)}]
            set T13 0.0
            set T21 [expr {sin($psi)}]
            set T22 [expr {cos($psi)}]
            set T23 0.0
            set T31 0.0
            set T32 0.0
            set T33 1.0
            # Its time derivative is:
            #   dT/dt = [ -ω·sin(ψ)   -ω·cos(ψ)   0.0 ;
            #             ω·cos(ψ)   -ω·sin(ψ)   0.0 ;
            #             0.0         0.0       0.0 ]
            set dT11 [expr {-1.0 * $w * sin($psi)}]
            set dT12 [expr {-1.0 * $w * cos($psi)}]
            set dT13 0.0
            set dT21 [expr {$w * cos($psi)}]
            set dT22 [expr {-1.0 * $w * sin($psi)}]
            set dT23 0.0
            set dT31 0.0
            set dT32 0.0
            set dT33 0.0

            return [list $T11 $T12 $T13 \
                         $T21 $T22 $T23 \
                         $T31 $T32 $T33 \
                         $dT11 $dT12 $dT13 \
                         $dT21 $dT22 $dT23 \
                         $dT31 $dT32 $dT33]
        }
    }
    """

    tcl_strings["energy"] = "Oxs_TransformZeeman"
    tcl_strings["type"] = "general"
    tcl_strings["script_args"] = "total_time"
    tcl_strings["script_name"] = f"TimeFunction:{drive_name}"

    return tcl_strings
