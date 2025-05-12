import micromagneticmodel as mm

def ampere_per_metre(target, energy_term_name='zeeman', field="H", units="Tesla"):
    """
    Convert magnetic field values from the specified units to amperes per metre (A/m).

    This function converts the field values stored in an energy term (or in a Zeeman
    energy field) to A/m. By default, the field values are assumed to be in Tesla
    and are converted using

        H [A/m] = H [Tesla] / μ0

    where μ0 is the permeability of free space (mm.consts.mu0). When the input field is
    already in A/m (units="A/m"), no conversion is performed.

    Additionally, if a plain list (or tuple) is passed as the target, the function will
    return a converted sequence of the same type.

    Parameters
    ----------
    target : mm.Energy or mm.Zeeman or list or tuple
        The micromagnetic energy term containing the field to convert. If target is an
        instance of mm.Energy, the energy term (default name 'zeeman') is accessed via
        target.__getattr__(energy_term_name) and the field is taken from its dictionary.
        If target is an instance of mm.Zeeman, the field is extracted from its __dict__.
        Alternatively, target can be a plain sequence (list or tuple) of field values.
    energy_term_name : str, optional
        The name of the energy term to convert (when target is an mm.Energy). Default is 'zeeman'.
    field : str, optional
        The attribute name for the field to convert (e.g. "H"). Default is "H".
    units : str, optional
        The units in which the field values are provided. Supported values:
          - "Tesla": Field values (in Tesla) are converted to A/m.
          - "A/m": Field values are assumed to already be in A/m.
        Default is "Tesla".

    Returns
    -------
    None or list/tuple
        If target is an mm.Energy or mm.Zeeman, the function updates the field in place and returns None.
        If target is a plain sequence (list or tuple), the function returns the converted sequence.

    Raises
    ------
    TypeError
        If target is not an instance of mm.Energy, mm.Zeeman, list, or tuple.
    ValueError
        If the provided units are not supported.

    Examples
    --------
    >>> # Convert a Zeeman energy field specified in Tesla to A/m:
    >>> ampere_per_metre(my_energy, energy_term_name='zeeman', field="H", units="Tesla")
    >>>
    >>> # When field values are already in A/m, no conversion occurs:
    >>> ampere_per_metre(my_energy, energy_term_name='zeeman', field="H", units="A/m")
    >>>
    >>> # Convert a list of field values from Tesla to A/m:
    >>> converted = ampere_per_metre([1e-3, 2e-3, 3e-3], units="Tesla")
    >>> # 'converted' will be a list of values in A/m.
    """
    def _convert_sequence(field_vals):
        # Convert field values based on provided units.
        if units.lower() == "tesla":
            converted = [val / mm.consts.mu0 for val in field_vals]
        elif units.lower() == "a/m":
            converted = [val for val in field_vals]
        else:
            raise ValueError("Units not recognized. Supported units are 'Tesla' and 'A/m'.")
        # Preserve the original sequence type.
        return converted if isinstance(field_vals, list) else tuple(converted)

    # If a plain sequence (list or tuple) is provided, convert and return it.
    if isinstance(target, (list, tuple)):
        return tuple(_convert_sequence(target))

    # Obtain the field from the target object.
    if isinstance(target, mm.Energy):
        # Access the energy term via the provided name.
        target_field = target.__getattr__(energy_term_name).__dict__[field]
    elif isinstance(target, mm.Zeeman):
        target_field = target.__dict__[field]
    else:
        raise TypeError('Unknown type of energy term; expected mm.Energy, mm.Zeeman, list, or tuple.')

    # If the field is stored as a dictionary (e.g. per region), convert each value.
    if isinstance(target_field, dict):
        for key, values in target_field.items():
            target_field[key] = _convert_sequence(values)
        return

    # If the field is a list or tuple, perform the conversion.
    if isinstance(target_field, (list, tuple)):
        converted = _convert_sequence(target_field)
        if isinstance(target, mm.Energy):
            target.__getattr__(energy_term_name).__dict__[field] = converted
        elif isinstance(target, mm.Zeeman):
            target.__dict__[field] = converted
        return

    raise TypeError('Unknown type for energy term field; expected dict, list, or tuple.')