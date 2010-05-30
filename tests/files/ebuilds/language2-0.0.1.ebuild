# Copyright 1999-2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# This ebuild was generated by g-octave

EAPI="3"

inherit octave-forge

DESCRIPTION="This is the Language 2 description"
HOMEPAGE="http://language2.org"
SRC_URI="mirror://sourceforge/octave/${OCT_P}.tar.gz"

LICENSE="|| ( GPL-2 GPL-3 LGPL BSD GFDL )"
SLOT="0"
KEYWORDS="~amd64 ~x86"
IUSE=""

# it's annoying have to see the download of packages from the official
# mirrors fail with a 404 error.
RESTRICT="mirror"

DEPEND=">sci-mathematics/pkg8-1.0.0
	>=sci-mathematics/pkg5-4.3.2
	<sci-mathematics/pkg6-1.2.3
	sci-mathematics/pkg7"
RDEPEND="${DEPEND}
	>=sci-mathematics/octave-3.2.0"
