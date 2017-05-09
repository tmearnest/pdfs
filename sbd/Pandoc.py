def detex(tex):
    """Use pandoc (if available) to modify LaTeX text strings
    for use as plain text, e.g. as printed to the terminal. Taken
    from original code in Rivet (http://rivet.hepforge.org), hence
    the particle physics bias in the macros used to do the replacements!

    TODO: Maybe group many strings to be processed together, to 
    save on system call / pandoc startup?
    """

    from distutils.spawn import find_executable
    if not find_executable("pandoc"):
        return tex
    texheader = r"""
    \newcommand{\text}[1]{#1}
    \newcommand{\ensuremath}[1]{#1}
    \newcommand{\emph}[1]{_#1_}
    \newcommand{\textrm}[1]{#1}
    \newcommand{\textit}[1]{_#1_}
    \newcommand{\textbf}[1]{*#1*}
    \newcommand{\mathrm}[1]{#1}
    \newcommand{\mathit}[1]{_#1_}
    \newcommand{\mathbf}[1]{*#1*}
    \newcommand{\bm}[1]{*#1*}
    \newcommand{\frac}[2]{#1/#2}
    \newcommand{\sqrt}[1]{sqrt(#1)}
    \newcommand{\hat}[1]{#1hat}
    \newcommand{\bar}[1]{#1bar}
    \newcommand{\d}[1]{d#1}
    \newcommand{\degree}{^\circ }
    \newcommand{\infty}{oo }
    \newcommand{\exp}{exp }
    \newcommand{\log}{log }
    \newcommand{\ln}{ln }
    \newcommand{\sin}{sin }
    \newcommand{\cos}{cos }
    \newcommand{\tan}{tan }
    \newcommand{\sinh}{sinh }
    \newcommand{\cosh}{cosh }
    \newcommand{\tanh}{tanh }
    \newcommand{\ell}{l}
    \newcommand{\varphi}{\phi}
    \newcommand{\varepsilon}{\epsilon}
    \newcommand{\sim}{~}
    \newcommand{\lesssim}{<~ }
    \newcommand{\gtrsim}{>~ }
    \newcommand{\neq}{!= }
    \newcommand{\ge}{>= }
    \newcommand{\gg}{>> }
    \newcommand{\le}{<= }
    \newcommand{\ll}{<< }
    \newcommand{\pm}{+- }
    \newcommand{\mp}{-+ }
    \newcommand{\times}{x }
    \newcommand{\cdot}{. }
    \newcommand{\langle}{<}
    \newcommand{\rangle}{>}
    \newcommand{\gets}{<- }
    \newcommand{\to}{-> }
    \newcommand{\leftarrow}{<- }
    \newcommand{\rightarrow}{-> }
    \newcommand{\leftrightarrow}{<-> }
    \newcommand{\Leftarrow}{<= }
    \newcommand{\Rightarrow}{=> }
    \newcommand{\Leftrightarrow}{ }
    \newcommand{\left}{}
    \newcommand{\right}{}
    \newcommand{\!}{}
    \newcommand{\/}{}
    \newcommand{\rm}{}
    \newcommand{\it}{}
    \newcommand{\,}{ }
    \newcommand{\;}{ }
    \newcommand{\ }{ }
    \newcommand{\unit}[2]{#1 #2}
    \newcommand{\bar}[1]{#1bar}
    \newcommand{\pT}{pT }
    \newcommand{\perp}{T}
    \newcommand{\MeV}{MeV }
    \newcommand{\GeV}{GeV }
    \newcommand{\TeV}{TeV }
    """
    import subprocess, shlex
    p = subprocess.Popen(shlex.split("pandoc -f latex -t plain --wrap=none"),
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    plain, err = p.communicate((texheader + tex).replace("\n", "").encode())
    plain = plain.decode().replace(r"\&", "&")
    # TODO: Replace \gamma, \mu, \tau, \Upsilon, \rho, \psi, \pi, \eta, \Delta, \Omega, \omega?
    # TODO: Replace e^+- -> e+-?
    return plain[:-1] if plain[-1] == "\n" else plain

# print detex(r"Foo \! $\int \text{bar} \d{x} \sim \; \frac{1}{3} \neq \emph{foo}$ \to \gg bar")
# => 'Foo \int bar dx ~ 1/3 != _foo_ -> >> bar'
