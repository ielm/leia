

class Aspect(object):
    """
    duration-aspect 	sem
            prolonged
            momentary
    iteration 	sem
            multiple
            single
    parametric-relation 	sem
            event
            object
    parametric-scalar 	sem
            (=>=< 0 1)
    phase 	sem
            begin-continue-end
            begin
            end
            continue
    scope 	sem
        event
        object
    """

    raise NotImplementedError


class Modality(object):

    """
    attributed-to 	sem
        human
        organization
        deity
    onto-instances 	value
        modality-2
        modality-1
    parametric-literal-attribute 	sem
        any-string
    parametric-relation 	sem
        event
        object
    parametric-scalar 	sem
        (=>=< 0 1)
    scope 	sem
        property
        event
        object
    type 	sem
        disjunctive
        conjunctive
        epistemic
        evaluative
        intentional
        obligative
        permissive
        potential
        saliency
        volitive
        ability
        belief
        effort
    value 	sem
        (=>=< 0 1)
    """

    raise NotImplementedError


class Set(object):

    """

    complete 	sem
        yes
        no
    determinate 	sem
        yes
        no
    elements 	sem
        event
        object
    member-type 	sem
        event
        object
    not-elements 	sem
        event
        object
    onto-instances 	value
        set-1
        set-2
    ordinality 	sem
        any-number
    parametric-literal-attribute 	sem
        any-string
    parametric-relation 	sem
        event
        object
    parametric-scalar 	sem
        (=>=< 0 1)
    power-set 	sem
        yes
        no
    relative-to-norm 	sem
        (=>=< 0 1)
    subset 	sem
        set
    type 	sem
        volitive
        saliency
        potential
        permissive
        obligative
        intentional
        evaluative
        epistemic
        effort
        disjunctive
        conjunctive
        belief
        ability

    """

    raise NotImplementedError