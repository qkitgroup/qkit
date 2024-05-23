''' The working point module has the purpose to a complete working point of a
    spin-transistor or similar. It works nicely in combination with the adwin,
    because it controls all parameters of a qorking point. So far this are:
        * magnetic fields (either cartesian or spherical coordinates)
            -> this module handles the translation from the abstract spherical
               representation to the cartesian 3D vector magnets used in the 
               experiment
        * voltages applied to the transistor

    ToDO:   * No init values for magnetic field and error handling if no valid
              values are set by the user. (this makes sure that after a restart
              of the software the magnetic fields are not accidently turned off
              but the user has to set explisit values in the measurement script
              ).
    '''

__all__ = ['VectorMagnet3D', 'WorkingPoint']
__version__ = '0.1_20240515'
__author__ = 'Luca Kosche'

from numpy import cos, sin, pi, NaN

class MagnetUnderdefinedError(Exception):
    """ Error which is thrown when the VectorMagnet has not enough
        parameters to calculate """

def grad2rad(grad):
    """ Transform angle in grad to rad """
    return grad * 2 * pi / 360

class VectorMagnet3D():
    ''' The vectormagnet class is designed to translate 3D B-field
        vectors in spherical coordinates to experimentally applicable
        cartesian coordinates of the 3D Vector magnet.
        There are two supported modes: "sweep" and "normal" mode.
        "sweep": THETA and PHI and Bp define the direction and length of
                 the magnetic field to be swept. The transverse field
                 direction is a linear combination of the unit vectors
                 in spherical cordinates e_theta and e_phi and defined
                 by the angle PSI. The length is defined by Bt.
        "normal": THETA and PHI define the direction of the transverse
                  Field whereas psi defines the direction of Bp.
                  This allows to sweep Bp in the normal plane defines by
                  Bt leaving the transverse field direction constant
                  (not possible in sweep mode).
               
          z |      / Bp
            |theta/.
            |    / .
            |   /  .
            |  /   .
            | /    .
            |/_____.____ y
            /  .   .
           /     . .
          /	phi    . 
       x /

    '''
    def __init__(self, mode=None, **kwargs):
        self._mode = mode
        self._sph = {'theta': 0,
                     'phi': 0,
                     'psi': 0,
                     'bp': 0,
                     'bt': 0}
        self.set_sph(**kwargs)

        #dynamically create properties
        for n in self._sph:
            setattr(
                VectorMagnet3D,
                n,
                property(
                    fget=lambda self, var=n: self.get_vec(var),
                    fset=lambda self, val, var=n: self.set_vec(var, val)
                )
            )

    def set_vec(self, var, val):
        ''' setter function for var of vector3d vector '''
        self._sph[var] = val

    def get_vec(self, var):
        ''' getter function for var of vector3d vector '''
        return self._sph[var]

    def set_sph(self, **kwargs):
        ''' update all given spherical b parameters '''
        for key, val in kwargs.items():
            self._sph[key] = val

    def calc_cartesian(self, **kwargs):
        ''' Use the current magnet field setpoint to calculate the
            cartesian magnetic field values, if all needed variables
            are there available '''
        # Update if new values are given
        self.set_sph(**kwargs)
        # All necessary parameters given to calculate cartesian vector?
        if self._mode is None:
            raise MagnetUnderdefinedError
        if None in self._sph.values():
            raise MagnetUnderdefinedError

        theta = grad2rad(self._sph['theta'])
        phi = grad2rad(self._sph['phi'])
        psi = grad2rad(self._sph['psi'])
        bp = self._sph['bp']
        bt = self._sph['bt']

        if self._mode == 'sweep':
            # caclulate
            bp_vec = (
                bp * sin(theta) * cos(phi),
                bp * sin(theta) * sin(phi),
                bp * cos(theta)
            )
            # calculate Bt as linear comb. of E_theta and E_phi
            # Bt_vec =  Bt * ( cos(psi) * E_theta + sin(psi)  * E_phi )
            bt_vec = (
                bt * (cos(psi) * cos(theta) * cos(phi) - sin(psi) * sin(phi)),
                bt * (cos(psi) * cos(theta) * sin(phi) + sin(psi) * cos(phi)),
                bt * -cos(psi) * sin(theta)
            )

        elif self._mode == 'normal':
            # caclulate Bt
            bt_vec = (
                bt * sin(theta) * cos(phi),
                bt * sin(theta) * sin(phi),
                bt * cos(theta)
            )
            # calculate Bp as linear comb. of E_theta and E_phi
            # Bp_vec =  Bp * ( cos(psi) * E_theta + sin(psi)  * E_phi )
            bp_vec = (
                bp * (cos(psi) * cos(theta) * cos(phi) - sin(psi) * sin(phi)),
                bp * (cos(psi) * cos(theta) * sin(phi) + sin(psi) * cos(phi)),
                bp * -cos(psi) * sin(theta)
            )
        # cartesian = superpostion of parallel and transverse field
        b_vec = (bp_vec[0] + bt_vec[0],
                 bp_vec[1] + bt_vec[1],
                 bp_vec[2] + bt_vec[2])
        # return as tuple for safety reasons (harder to mess up later)
        return b_vec

class WorkingPoint(VectorMagnet3D):
    ''' The working point describes a set of output values using dict
        If magnet="cartesian" magnetic field are just set as target
        values for the outputs of the coils.
        If magnet="vector3d" the channels "bx", "by", "bz" must be
        configured as output channels. When asking for the outputs with
        property "outs", the cartesian fields will be calculated '''
    def __init__(self, output_names, wp=None, magnet='cartesian'):
        if magnet in ['cartesian', 'vector3d']:
            self._magnet = magnet
        else:
            raise TypeError
        if magnet == 'vector3d':
            super().__init__(mode='sweep')
        self._outputs = {key: NaN for key in output_names}
        if wp is not None:
            self.set_wp(**wp)
        self._create_properties(output_names)

    @property
    def outs(self):
        ''' the outputs property '''
        if self._magnet == 'vector3d':
            self.set_b(self.calc_cartesian())
        return self._outputs

    def set_out(self, name: str, value: float):
        ''' setter function for output "name" '''
        if self._magnet == 'vector3d' and name in ['bx', 'by', 'bz']:
            print(f'WARNING: vector3D will overwrite {name}!' )
        self._outputs[name] = value

    def get_out(self, name: str):
        ''' getter function for output "name" '''
        return self._outputs[name]

    def set_wp(self, **kwargs):
        ''' set multiple outputs with a single function call '''
        for key, val in kwargs.items():
            if key in self._outputs.keys():
                self.set_out(key, val)
            else:
                print(f'working point: output {key} not configured. IGNORED!')

    def set_b(self, b_fields: tuple):
        ''' Set magnetic field setpoints from tuple (to not mess up).
            Preferably from VectorMagnet3D.calc_cartesian() '''
        bdict = {'0': 'bx', '1': 'by', '2': 'bz'}
        for idx, val in enumerate(b_fields):
            name = bdict[str(idx)]
            self._outputs[name] = val

    def _create_properties(self, names):
        ''' dynamically create properties for all output names '''
        for n in names:
            setattr(
                WorkingPoint,
                n,
                property(
                    fget=lambda self, var=n: self.get_out(var),
                    fset=lambda self, val, var=n: self.set_out(var, val)
                )
            )

if __name__ == '__main__':
    pass
