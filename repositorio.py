from database import colecao


def listar_disciplinas():
    return sorted(colecao.distinct("disciplina"))


def listar_topicos(disciplina):
    return sorted(
        colecao.distinct(
            "topico",
            {"disciplina": disciplina}
        )
    )


def listar_assuntos(disciplina, topico):
    return sorted(
        colecao.distinct(
            "assunto",
            {
                "disciplina": disciplina,
                "topico": topico
            }
        )
    )


def listar_questoes(disciplina, topico, assunto):
    filtro = {
        "disciplina": disciplina,
        "topico": topico,
        "assunto": assunto
    }

    return list(
        colecao.find(filtro).sort("_id", 1)
    )