FROM andrewosh/binder-base

MAINTAINER Daniel Wheeler <daniel.wheeler2@gmail.com>

USER root

RUN apt-get -y update
RUN apt-get install -y bzip2 g++ libgfortran3 liblapack3 git
RUN apt-get clean

USER main

RUN wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh
RUN /bin/bash ~/miniconda.sh -b -p ~/anaconda3
RUN rm ~/miniconda.sh
ENV PATH /home/main/anaconda3/bin:$PATH
RUN conda config --set always_yes yes --set changeps1 no
RUN conda update -q conda
RUN conda install -q -y numpy scipy pytest pandas pytables jupyter
RUN conda install -q -y cython matplotlib jupyter toolz
RUN pip install sumatra scikit-fmm
RUN git clone https://github.com/usnistgov/fipy.git ~/fipy
WORKDIR /home/main/fipy
RUN 2to3 --write .
RUN python setup.py install
WORKDIR /home/main
RUN git clone https://github.com/wd15/extremefill2D
WORKDIR /home/main/extremefill2D
RUN python setup.py install


ENV SHELL /bin/bash
