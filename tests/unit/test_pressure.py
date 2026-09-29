"""pressure.py testlari -- churn tartibi va tezlik oynasi.

Bu testlar xotira ajratadi, lekin JUDA KICHIK (bir necha MB) va cgroup
chegarasi yo'q -- ular mexanizmni sinaydi, pressure yaratmaydi.
"""
from revix.pressure import Allocator


def test_churn_avval_ajratadi_keyin_boshatadi():
    """Tartib muhim: bo'shat->ajrat bo'lsa memory.high dan hech qachon oshmaydi
    va pressure umuman bo'lmaydi. Bu test shu regressiyani qulflaydi."""
    a = Allocator()
    block = 1 << 20  # 1 MB
    a.add(block)
    assert len(a.blocks) == 1

    # Ajratish paytida blok soni VAQTINCHA oshishi kerak.
    seen = []
    orig_add = a.add

    def spy_add(n):
        orig_add(n)
        seen.append(len(a.blocks))

    a.add = spy_add  # type: ignore[method-assign]
    a.churn(1, block)
    # add chaqirilganda 2 blok bo'lgan (vaqtincha oshish), keyin 1 ga qaytgan
    assert seen == [2], f"ajratish paytida vaqtincha oshish kutildi, {seen} bo'ldi"
    assert len(a.blocks) == 1, "churn'dan keyin blok soni o'zgarmasligi kerak"
    a.release_all()


def test_churn_umumiy_hajmni_oshirmaydi():
    """Churn o'sishsiz bo'lishi kerak, aks holda MemoryMax'ga yetib OOM bo'ladi."""
    a = Allocator()
    block = 1 << 20
    for _ in range(4):
        a.add(block)
    before = a.touched_bytes
    a.churn(10, block)
    assert a.touched_bytes == before, "churn net o'sish bermasligi kerak"
    a.release_all()


def test_churn_bosh_allocator_da_ishlaydi():
    """Birinchi churn'da bo'shatiladigan eski blok yo'q -- yiqilmasligi kerak.

    Bo'sh allocator'dan churn barqaror holatga intiladi: birinchi ajratish
    saqlanadi, keyingilari almashtiriladi. Haqiqiy ishlatishda baza allaqachon
    ajratilgan bo'ladi, shuning uchun bu chegaraviy holat.
    """
    a = Allocator()
    block = 1 << 20
    n = a.churn(2, block)
    assert n == 2, "ikkala churn ham bajarilishi kerak"
    assert len(a.blocks) == 1, "churn barqaror holatga intiladi"
    assert a.touched_bytes == block
    a.release_all()


def test_release_all_hisobni_tiklaydi():
    a = Allocator()
    a.add(1 << 20)
    a.release_all()
    assert a.touched_bytes == 0
    assert a.blocks == []
