# Project

ISAdetect - "ML-based ISA detection (architecture and endianness of binary code/sequences)"

## Referencing

If/when using code and/or data from this project (direct, derivative works),
please don't forget to reference the following:

```
@inproceedings{kairajarvi2020isadetect,
author={Kairaj\"arvi, Sami and Costin, Andrei and H\"am\"al\"ainen, Timo},
title={{ISAdetect: Usable automated detection of ISA (CPU architecture and endianness) for executable binary files and object code}},
booktitle={Proceedings of the Tenth ACM Conference on Data and Application Security and Privacy},
year={2020},
url="https://doi.org/10.1145/3374664.3375742"
}
```

```
@article{kairajarvi2019towards,
	title={{Towards usable automated detection of CPU architecture and endianness for arbitrary binary files and object code sequences}},
	author={Kairaj\"arvi, Sami and Costin, Andrei and H\"am\"al\"ainen, Timo},
	journal={arXiv preprint arXiv:1908.05459},
	year={2019},
    howpublished =   "\url{http://arxiv.org/abs/1908.05459}",
    url =   "http://arxiv.org/abs/1908.05459",
}
```
```
@MastersThesis{Kairajarvi:Thesis:2019,
    author     =     {Kairaj\"arvi, Sami},
    title     =     {{Automatic identification of architecture and endianness using binary file contents}},
    school     =     {University of Jyv\"askyl\"a},
    address     =     {Jyv\"askyl\"a, Finland},
    year     =     {2019},
    publisher   =   {JYX Digital Repository},
    howpublished =   "\url{http://urn.fi/URN:NBN:fi:jyu-201904182217}",
    url =   "http://urn.fi/URN:NBN:fi:jyu-201904182217",
}
```

## Directory structure

ml: Machine Learning related scripts: training, generating ML model.

api: Exposing the ML classification as RESTful API via Swagger/OpenAPI.

dataset_gen: Set of tools and scripts to gather and compile the datasets.

plugins: Plugins that call the RESTful API from SotA tools such as radare2 and IDAPro.

## Dataset

Dataset related to this project can be found at https://etsin.fairdata.fi/dataset/03fe55df-a1bb-4d24-8c8b-eb12eb3b74f1 (http://urn.fi/urn:nbn:fi:att:4dbe7751-bab9-47be-85d1-bf535a23b59a)

## Questions and comments

Please feel free to submit an issue on Github for any questions or concerns.
