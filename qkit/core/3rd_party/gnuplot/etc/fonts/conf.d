<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>

<!--
  Set fonts to be preferred when the standard aliases "serif", "sans-serif",
  and "monospace" are used.
-->

	<alias>
		<family>serif</family>
		<prefer>
			<family>Times New Roman</family>
			<family>Thorndale AMT</family>
			<family>DejaVu Serif</family>
			<family>Liberation Serif</family>
			<family>SUSE Serif</family>
			<family>Bitstream Vera Serif</family>
			<family>Nimbus Roman No9 L</family>
			<family>Luxi Serif</family>
			<family>Likhan</family>
			<family>KacstBook</family>
			<family>Frank Ruehl CLM</family>
			<family>Times</family>
			<family>Khmer OS System</family>
			<family>Lohit Punjabi</family>
			<family>Lohit Oriya</family>
			<family>Pothana2000</family>
			<family>TSCu_Times</family>
			<family>BPG Chveulebrivi</family>
			<family>Nazli</family>
			<family>FreeSerif</family>
			<family>MS PMincho</family>
			<family>MS Mincho</family>
			<family>HGPMinchoL</family>
			<family>HGMinchoL</family>
			<family>IPAPMincho</family>
			<family>IPAMincho</family>
			<family>Sazanami Mincho</family>
			<family>Kochi Mincho</family>
			<family>CMEXSong</family>
			<family>FZSongTi</family>
			<family>WenQuanYi Zen Hei</family>
			<family>AR PL ShanHeiSun Uni</family>
			<family>FZMingTiB</family>
			<family>AR PL SungtiL GB</family>
			<family>AR PL Mingti2L Big5</family>
			<family>UnBatang</family>
			<family>Baekmuk Batang</family>
			<family>SimSun</family>
			<family>HanyiSong</family>
			<family>ZYSong18030</family>
		</prefer>
	</alias>
	<alias>
		<family>sans-serif</family>
		<prefer>
			<family>Arial</family>
			<family>Albany AMT</family>
			<family>Verdana</family>
			<family>DejaVu Sans</family>
			<family>Liberation Sans</family>
			<family>SUSE Sans</family>
			<family>Bitstream Vera Sans</family>
			<family>Nimbus Sans L</family>
			<family>Luxi Sans</family>
			<family>Mukti Narrow</family>
			<family>KacstBook</family>
			<family>Nachlieli CLM</family>
			<family>Helvetica</family>
			<family>Khmer OS System</family>
			<family>Lohit Punjabi</family>
			<family>Lohit Oriya</family>
			<family>Pothana2000</family>
			<family>TSCu_Paranar</family>
			<family>BPG Glaho</family>
			<family>Terafik</family>
			<family>FreeSans</family>
			<family>Meiryo</family>
			<family>MS PGothic</family>
			<family>MS Gothic</family>
			<family>HGPGothicB</family>
			<family>HGGothicB</family>
			<family>IPAPGothic</family>
			<family>IPAGothic</family>
			<family>VL PGothic</family>
			<family>VL Gothic</family>
			<family>Sazanami Gothic</family>
			<family>Kochi Gothic</family>
			<family>CMEXSong</family>
			<family>FZSongTi</family>
			<family>WenQuanYi Zen Hei</family>
			<family>AR PL ShanHeiSun Uni</family>
			<family>FZMingTiB</family>
			<family>AR PL SungtiL GB</family>
			<family>AR PL Mingti2L Big5</family>
			<family>UnDotum</family>
			<family>Baekmuk Gulim</family>
			<family>Baekmuk Dotum</family>
		</prefer>
	</alias>
	<alias>
		<family>monospace</family>
		<prefer>
			<family>Consolas</family>
			<family>Andale Mono</family>
			<family>DejaVu Sans Mono</family>
			<family>Liberation Sans</family>
			<family>SUSE Sans Mono</family>
			<family>Bitstream Vera Sans Mono</family>
			<family>Courier New</family>
			<family>Cumberland AMT</family>
			<family>Nimbus Mono L</family>
			<family>Luxi Mono</family>
			<family>Mukti Narrow</family>
			<family>KacstBook</family>
			<family>Miriam Mono CLM</family>
			<family>Terafik</family>
			<family>Khmer OS System</family>
			<family>Lohit Punjabi</family>
			<family>Lohit Oriya</family>
			<family>Pothana2000</family>
			<family>TSCu_Paranar</family>
			<family>BPG Courier</family>
			<family>FreeMono</family>
			<family>MS Gothic</family>
			<family>HGGothicB</family>
			<family>IPAGothic</family>
			<family>VL Gothic</family>
			<family>Sazanami Gothic</family>
			<family>Kochi Gothic</family>
			<family>CMEXSong</family>
			<family>FZSongTi</family>
			<family>WenQuanYi Zen Hei Mono</family>
			<family>AR PL ShanHeiSun Uni</family>
			<family>FZMingTiB</family>
			<family>AR PL SungtiL GB</family>
			<family>AR PL Mingti2L Big5</family>
			<family>UnDotum</family>
			<family>Baekmuk Gulim</family>
			<family>Baekmuk Dotum</family>
			<family>NSimSun</family>
			<family>HanyiSong</family>
			<family>ZYSong18030</family>
		</prefer>
	</alias>

<!--
 For fonts which have good byte code, one should always use
 the byte code interpreter if anti-aliasing is off.
 When anti-aliasing is on, people apparently disagree whether these
 fonts look better with the auto-hinter or the byte code interpreter.
 But when anti-aliasing is off, it is obvious that using the
 byte code interpreter is better.
 This has to be limited to a list of fonts which are known
 to have good byte though, most fonts do *not* have good byte code
 and render better with the autohinter even if anti-aliasing is off
 (See "FreeSans" for example, it obviously looks better with the
 autohinter when anti-aliasing is off).
-->

        <match target="font">
                <test name="family">
                        <string>Andale Mono</string>
                        <string>Arial</string>
                        <string>Comic Sans MS</string>
                        <string>Georgia</string>
                        <string>Impact</string>
                        <string>Trebuchet MS</string>
                        <string>Verdana</string>
                        <string>Courier New</string>
                        <string>Times New Roman</string>
                        <string>Tahoma</string>
                        <string>Webdings</string>
                        <string>Albany AMT</string>
                        <string>Thorndale AMT</string>
                        <string>Cumberland AMT</string>
                        <string>Andale Sans</string>
                        <string>Andy MT</string>
                        <string>Bell MT</string>
                        <string>Monotype Sorts</string>
                        <string>Lucida Sans Typewriter</string>
                        <string>Lucida Sans</string>
                        <string>Lucida Bright</string>
                </test>
		<test name="antialias">
                        <bool>false</bool>
		</test>
                <edit name="autohint">
                        <bool>false</bool>
                </edit>
        </match>

</fontconfig>

