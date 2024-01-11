Summary:        Performs a verified launch using Intel TXT
Name:           tboot
Version:        1.10.5
Release:        2%{?dist}
Epoch:          1

License:        BSD
URL:            http://sourceforge.net/projects/tboot/
Source0:        http://downloads.sourceforge.net/%{name}/%{name}-%{version}.tar.gz

Patch01: 0001-fix-typo-in-lcp2_crtpollist-manpage.patch
Patch02: 0002-check-for-client-server-match.patch

BuildRequires:  make
BuildRequires:  gcc
BuildRequires:  perl
BuildRequires:  openssl-devel
BuildRequires:  zlib-devel
ExclusiveArch:  %{ix86} x86_64
Requires:  	grub2-efi-x64-modules

%description
Trusted Boot (tboot) is an open source, pre-kernel/VMM module that uses
Intel Trusted Execution Technology (Intel TXT) to perform a measured
and verified launch of an OS kernel/VMM.

%prep
%autosetup -p1 -n %{name}-%{version}

%build
CFLAGS="%{optflags}"; export CFLAGS
LDFLAGS="%{build_ldflags}"; export LDFLAGS
make debug=y %{?_smp_mflags}

%post
# Rmove the grub efi modules if they had been placed in the wrong directory by
# a previous install.
[ -d /boot/efi/EFI/redhat/x86_64-efi ] && rm -rf /boot/efi/EFI/redhat/x86_64-efi
# create the tboot grub entry
grub2-mkconfig -o /boot/grub2/grub.cfg

# For EFI based machines ...
if [ -d /sys/firmware/efi ]; then
	echo "EFI detected .."
	[ -d /boot/grub2/x86_64-efi ] || mkdir -pv /boot/grub2/x86_64-efi
	cp -vf /usr/lib/grub/x86_64-efi/relocator.mod /boot/grub2/x86_64-efi/
	cp -vf /usr/lib/grub/x86_64-efi/multiboot2.mod /boot/grub2/x86_64-efi/

	# If there were a previous install of tboot that overwrote the
	# originally installed /boot/efi/EFI/redhat/grub.cfg stub, then
	# recreate it.
	if grep -q -m1 tboot /boot/efi/EFI/redhat/grub.cfg; then
cat << EOF > /boot/efi/EFI/redhat/grub.cfg
search --no-floppy --fs-uuid --set=dev \
	$(lsblk -no UUID $(df -P /boot/grub2 | awk 'END{print $1}'))
set prefix=(\$dev)/grub2
export \$prefix
configfile \$prefix/grub.cfg
EOF
		chown root:root /boot/efi/EFI/redhat/grub.cfg
		chmod u=rwx,go= /boot/efi/EFI/redhat/grub.cfg
	fi
fi

%postun
# Remove residual grub efi modules.
[ -d /boot/grub2/x86_64-efi ] && rm -rf /boot/grub2/x86_64-efi
[ -d /boot/efi/EFI/redhat/x86_64-efi ] && rm -rf /boot/efi/EFI/redhat/x86_64-efi
grub2-mkconfig -o /etc/grub2.cfg

%install
make debug=y DISTDIR=$RPM_BUILD_ROOT install

%files
%doc README.md COPYING docs/* lcptools-v2/lcptools.txt
%config %{_sysconfdir}/grub.d/20_linux_tboot
%config %{_sysconfdir}/grub.d/20_linux_xen_tboot
%{_sbindir}/txt-acminfo
%{_sbindir}/lcp2_crtpol
%{_sbindir}/lcp2_crtpolelt
%{_sbindir}/lcp2_crtpollist
%{_sbindir}/lcp2_mlehash
%{_sbindir}/txt-parse_err
%{_sbindir}/tb_polgen
%{_sbindir}/txt-stat
%{_mandir}/man8/txt-acminfo.8.gz
%{_mandir}/man8/tb_polgen.8.gz
%{_mandir}/man8/txt-stat.8.gz
%{_mandir}/man8/lcp2_crtpol.8.gz
%{_mandir}/man8/lcp2_crtpolelt.8.gz
%{_mandir}/man8/lcp2_crtpollist.8.gz
%{_mandir}/man8/lcp2_mlehash.8.gz
%{_mandir}/man8/txt-parse_err.8.gz
/boot/tboot.gz
/boot/tboot-syms

%changelog
* Thu Aug 18 2022 Tony Camuso <tcamuso@redhat.com> - 1:1.10.5-2
- The install scriptlet in %post was choosing the first grub.cfg
  file it encountered, which was /boot/efi/EFI/redhat/grub.cfg.
  This is a stub that defines grub boot disk UUID necessary for
  proper grubenv setup, and it must not be overwritten or changed.
  Modify the scriptlet to target /boot/grub2/grub.cfg
  Additionally, remove any wrongly created /boot/grub2/x86_64-efi
  directory and recreate the correct /boot/efi/EFI/redhat/grub.cfg
  stub file.
  Added a %postun section to cleanup when removing tboot with
  dnf erase.
  Thanks to Lenny Szubowicz for the bash code to recreate the
  /boot/efi/EFI/redhat/grub.cfg stub file.
  Resolves: rhbz#2112236

* Wed May 04 2022 Tony Camuso <tcamuso@redhat.com> - 1:1.10.5-1
- Upgrade to tboot-1.10.5-1 for fixes and updates.
- Added a Requires line to install grub2-efi-x64-modules
- Added a scriptlet to the tboot.spec file to automatically install
  grub2-efi-x64-modules and move them to the correct directory.
- Removed three patches that are no longer needed.
- Added two patches from upstream, one for a fix, the other cosemetic.
- Resolves: rhbz#2041766
  Resolves: rhbz#2040083

* Thu Sep 30 2021 Tony Camuso <tcamuso@redhat.com> - 1:1.10.2-6
- Use sha256 as default hashing algorithm
  Resolves: rhbz#1935448

* Tue Aug 10 2021 Mohan Boddu <mboddu@redhat.com> - 1:1.10.2-5
- Rebuilt for IMA sigs, glibc 2.34, aarch64 flags
  Related: rhbz#1991688

* Wed Jul 28 2021 Tony Camuso <tcamuso@redhat.com> - 1:1.10.2-4
- From Miroslave Vadkerti:
  Onboarding tests to RHEL9 in BaseOS CI requires action, adding
  test configuration in our "dispatcher" configuration for RHEL9:
  https://gitlab.cee.redhat.com/baseos-qe/citool-config/blob/production/brew-dispatcher-rhel9.yaml
  Test config was added for tboot in the following MR.
  https://gitlab.cee.redhat.com/baseos-qe/citool-config/-/merge_requests/2686
  Resolves: rhbz#1922002

* Tue Jul 27 2021 Tony Camuso <tcamuso@redhat.com> - 1:1.10.2-3
- Add the %{optflags} and %{build_ldflags} macros to assure the
  build meets RHEL security requirements.
  Resolves: rhbz#1922002

* Thu Jul 22 2021 Tony Camuso <tcamuso@redhat.com> - 1:1.10.2-2
- Bump the NVR as a result of including the gating.yaml file in
  the git repo.
  Resolves: rhbz#1922002

* Mon Jun 21 2021 Tony Camuso <tcamuso@redhat.com> - 1:1.10.2-1
- The patches are for SSL3 compatibility. These can probably be
  removed when upstream tboot fully implements SSL3.
- Upgrade to latest upstream.
- Remove trousers dependency.
  Resolves: rhbz#1922002
  Resolves: rhbz#1870520
  Resolves: rhbz#1927374

* Wed Jun 16 2021 Mohan Boddu <mboddu@redhat.com> - 1:1.9.11-9
- Rebuilt for RHEL 9 BETA for openssl 3.0
  Related: rhbz#1971065

* Thu May 27 2021 Tony Camuso <tcamuso@redhat.com> - 1:1.9.11-8
- Add -Wno-error=deprecated-declarations to the Config.mk patch
  Resolves: rhbz#1958031

* Fri Apr 16 2021 Mohan Boddu <mboddu@redhat.com> - 1:1.9.11-7
- Rebuilt for RHEL 9 BETA on Apr 15th 2021. Related: rhbz#1947937

* Wed Jan 27 2021 Fedora Release Engineering <releng@fedoraproject.org> - 1:1.9.11-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Fri Oct 30 2020 Jeff Law <law@redhat.com> - 1:1.9.11-5
- Re-enable -Wstringop-overflow and instead make the problematical
  pointer volatile to avoid the false positive diagnostic

* Thu Oct 29 2020 Jeff Law <law@redhat.com> - 1:1.9.11-4
- Fix buglet exposed by gcc-11 -Warray-parameter
- Temporarily disable -Wstringop-overflow due to false positive in gcc-11

* Wed Jul 29 2020 Jeff Law <law@redhat.com> - 1:1.9.11-3
- Explicitly allow uninitialized variables in a few places that do it
- on purpose

* Wed Jul 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1:1.9.11-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Sun Apr 19 2020 Filipe Rosset <rosset.filipe@gmail.com> - 1:1.9.11-1
- Update to 1.9.11

* Fri Jan 31 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1:1.9.10-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Sat Jul 27 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1:1.9.10-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Tue May 14 2019 Yunying Sun <yunying.sun@intel.com> - 1:1.9.10-1
- Add patch to fix package build error
- Add build dependency to zlib-devel
- Update to latest release 1.9.10

* Sun Feb 03 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1:1.9.8-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Wed Oct 31 2018 Yunying Sun <yunying.sun@intel.com> - 1:1.9.8-1
- Updated to upstream 1.9.8 release

* Tue Sep 4 2018 Yunying Sun <yunying.sun@intel.com> - 1:1.9.7-1
- Updated to upstream 1.9.7 release
- Removed the patch for openssl 1.1 as it is included in 1.9.7 already

* Sat Jul 14 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1:1.9.6-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Tue Feb 06 2018 Tomáš Mráz <tmraz@redhat.com> - 1:1.9.6-2
- Patch to build with OpenSSL-1.1.x

* Sun Feb 04 2018 Filipe Rosset <rosset.filipe@gmail.com> - 1:1.9.6-1
- Upgrade to latest upstream version

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1:1.8.2-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1:1.8.2-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1:1.8.2-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Fri Feb 05 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1:1.8.2-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Fri Jun 19 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.8.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Mon Aug 18 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.8.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Wed Jul 30 2014 Gang Wei <gang.wei@intel.com> - 1:1.8.2-1
- Upgrade to latest upstream version which provided security fix for:
  tboot:argument measurement vulnerablity for GRUB2+ELF kernels

* Wed Jun 18 2014 Gang Wei <gang.wei@intel.com> - 1:1.8.1-1
- Upgrade to latest upstream version

* Sun Jun 08 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.7.3-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Sun Aug 04 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.7.3-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Tue Apr 02 2013 Gang Wei <gang.wei@intel.com> - 1:1.7.3-3
- Fix for breaking grub2-mkconfig operation in 32bit case(#929384)

* Wed Feb 20 2013 Gang Wei <gang.wei@intel.com> - 1:1.7.3-2
- Fix version string in log

* Wed Jan 30 2013 David Cantrell <dcantrell@redhat.com> - 1:1.7.3-1
- Upgrade to latest upstream version (#902653)

* Wed Aug 22 2012 Gang Wei <gang.wei@intel.com> - 1:1.7.0-2
- Fix build error with zlib 1.2.7

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.7.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Sun Jan 15 2012 Gang Wei <gang.wei@intel.com> - 1:1.7.0
- 1.7.0 release

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 20110429-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Fri Apr 29 2011 Gang Wei <gang.wei@intel.com> - 20110429-1
- Pull upstream changeset 255, rebuilt in F15

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 20101005-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Wed Dec 1 2010 Joseph Cihula <joseph.cihula@intel.com> - 20101005-1.fc13
- Initial import
