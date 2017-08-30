# copyright Ηλιάδης Ηλίας 2014.
# contact http://gnu.kekbay.gr/OCPcompanion/  -- mailto:OCPcompanion@kekbay.gr
#
# This file is part of OCPcompanion.
#
# OCPcompanion is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3.0 of the License, or (at your option) any
# later version.
#
# OCPcompanion is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along
# with OCPcompanion.  If not, see <http://www.gnu.org/licenses/>.
'''Usefull graphical functions and constants.'''

__docformat__ = "restructuredtext en"
from .__pkginfo__ import version as __version__

from .AbstractGui import OCPAbstractGui as AbstractGui

from .configarser import MyConfigs as vbpPrivateProfile


__all__ = ['AbstractGui', 'vbpPrivateProfile']
