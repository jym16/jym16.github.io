---
title: Jupyter Notebook Demo with Julia
tags: programming Julia
---

## Set Up
1. Install the Julia Language. For details, refer [here](https://julialang.org/downloads/).
    - Mac: 

        e.g. homebrew.  
        ```
          $ brew install julia
        ```
    
    - Linux: Use the corresponding package manager. 

        e.g. Ubuntu
        ```
          $ sudo apt install julia
        ```
    
    - Windows: 

        Set up a Linux machine on [WSL2(Windows Subsystem for Linux 2)](https://docs.microsoft.com/en-us/windows/wsl/) or [Virtual Box](https://www.virtualbox.org/). 

2. Download the following file to your computer: [SchroedingerEquation1D.ipynb](/assets/codes/julia/ShroedingerEquation1D/SchroedingerEquation1D.ipynb)

3. Start Julia REPL. If you are new to Julia and want to learn about it, see [Getting Started](https://docs.julialang.org/en/v1/manual/getting-started/). 
    ```
        $ julia

                       _
           _       _ _(_)_     |  Documentation: https://docs.julialang.org
          (_)     | (_) (_)    |
           _ _   _| |_  __ _   |  Type "?" for help, "]?" for Pkg help.
          | | | | | | |/ _` |  |
          | | |_| | | | (_| |  |  Version 1.6.1 (2021-04-23)
         _/ |\__'_|_|_|\__'_|  |  Official https://julialang.org/ release
        |__/                   |


        julia>
    ```

4. Add the necessary packages. 
   1. Hit `]` key. Then you enter the Pkg REPL, where you can manage packages in your machine.
   2. Install `IJulia.jl`, `Plots.jl`, and `LinearAlgebra.jl`.
    ```
        (@v1.6) pkg> add IJulia Plots LinearAlgebra
    ```
   3. Move back the normal REPL by hitting `backspace` key.

5. Start the Jupyter notebook.
   ```
        julia> using IJulia
        julia> IJulia.notebook()
   ```

6. It will open the Jupyter notebook on your browser. 

## Jupyter Notebook

7. Navigate to the location where you downloaded the file in Step 2. (within the Jupyter notebook.)

8. Click the file and it should open another tab.

9. Then you can see the contents of the Jupyter notebook and play around with it.


In case you could not open the jupyter notebook, [here](/assets/codes/julia/ShroedingerEquation1D/SchroedingerEquation1D.html) is the exported html. (You cannot use interactively, but you can see how it will look. )

You can also export the notebook as a [pdf](/assets/codes/julia/ShroedingerEquation1D/SchroedingerEquation1D.pdf) using $\LaTeX$. 