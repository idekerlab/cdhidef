=======
History
=======

1.1.1b1 (2020-01-15)
------------------------------

* Updated to pull cdhidef.1.1.1b1 of https://github.com/coleslaw481/HiDeF

* Added ``--numthreads`` flag with default value set to ``4``. This is to support
  new ``--numthreads`` flag in HiDeF 1.1.1 beta

* Renamed ``--ct`` flag to ``--p`` to match HiDeF 1.1.1 beta

* Reduced ``--maxres`` default to ``25.0``

* No longer passing ``--skipclug`` flag to HiDeF since HiDeF 1.1.1 beta
  removed this option

* Switched default algorithm ``--alg`` to ``leiden``

0.2.2 (2020-08-12)
------------------------------

* Updated to pull cdhidef.0.2.2 of https://github.com/coleslaw481/HiDeF
  which fixed a bug where --alg leiden was failing

0.2.1 (2020-06-15)
------------------------------

* Updated to pull cdhidef.0.2.1 of https://github.com/coleslaw481/HiDeF

0.2.0 (2020-05-19)
------------------------------

* Updated to pull cdhidef.0.2.0 of https://github.com/coleslaw481/HiDeF

0.1.1 (2020-05-14)
------------------------------

* Updated to generate new output that includes
  custom new column

0.0.1 (2020-03-26)
------------------

* First release
