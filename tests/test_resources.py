import pytest
import pyecore.ecore as Ecore
from pyecore.ecore import *
from pyecore.resources import ResourceSet, URI, Resource, global_registry
from pyecore.resources import global_uri_converter, AbstractURIConverter
from pyecore.resources.resource import Global_URI_decoder
from pyecore.resources.resource import HttpURI
from pyecore.resources.xmi import XMIResource
from os import path


@pytest.fixture(scope='module')
def simplemm():
    A = EClass('A')
    B = EClass('B')
    Root = EClass('Root')
    Root.eStructuralFeatures.append(EReference('a', A, containment=True,
                                               upper=-1))
    Root.eStructuralFeatures.append(EReference('b', B, containment=True,
                                               upper=-1))

    A.eStructuralFeatures.append(EReference('tob', B, upper=-1))

    pack = EPackage('pack', nsURI='http://pack/1.0', nsPrefix='pack')
    pack.eClassifiers.extend([Root, A, B])
    pack.Root = Root
    pack.A = A
    pack.B = B
    return pack


def test_init_globalregistry():
    assert global_registry
    assert global_registry[Ecore.nsURI]


def test_resourceset_defaut_decoders():
    assert 'xmi' in ResourceSet.resource_factory
    assert 'ecore' in ResourceSet.resource_factory
    assert '*' in ResourceSet.resource_factory


def test_uri_empty():
    uri = URI('')
    assert uri.protocol is None
    assert uri.extension is None
    assert uri.plain == ''


def test_uri_none():
    with pytest.raises(TypeError):
        URI(None)


def test_uri_simple():
    uri = URI('http://test.ecore')
    assert uri.protocol == 'http'
    assert uri.extension == 'ecore'
    assert uri.plain == 'http://test.ecore'


def test_uri_noextension():
    uri = URI('http://test')
    assert uri.protocol == 'http'
    assert uri.extension is None
    assert uri.plain == 'http://test'


def test_uri_noprotocol():
    uri = URI('test.ecore')
    assert uri.protocol is None
    assert uri.extension == 'ecore'
    assert uri.plain == 'test.ecore'


def test_uri_noprotocol_noextension():
    uri = URI('test')
    assert uri.protocol is None
    assert uri.extension is None
    assert uri.plain == 'test'


def test_uri_normalize_virtual():
    uri = URI('http://virtual/1.0')
    assert uri.normalize() == 'http://virtual/1.0'


def test_uri_normalize_fileuri_abs():
    uri = URI('file:///test.xmi')
    assert path.isabs(uri.normalize())


def test_uri_normalize_fileuri_relative():
    xmi_path = path.join('tests', 'xmi', 'xmi-tests', 'testEMF.xmi')
    uri = URI('file://' + xmi_path)
    assert path.exists(uri.normalize())


def test_uri_normalize_relative():
    uri = URI(path.join('tests', 'xmi', 'xmi-tests', 'testEMF.xmi'))
    assert path.exists(uri.normalize())


def test_uri_normalize_httpuri():
    uri = HttpURI('http://www.test.org/path/xmi/')
    assert uri.normalize() == 'http://www.test.org/path/xmi/'

    assert uri.apply_relative_from_me('../mypath') == 'http://www.test.org/path/mypath'
    assert uri.apply_relative_from_me('../../mypath') == 'http://www.test.org/mypath'

    # Different URL
    assert uri.apply_relative_from_me('http://www.other.org/path/xmi') == 'http://www.other.org/path/xmi'

    # Same URL
    assert uri.apply_relative_from_me('http://www.test.org/path/xmi2') == 'http://www.test.org/path/xmi2'

    # without trailing "/"
    uri = HttpURI('http://www.test.org/path/xmi')
    assert uri.normalize() == 'http://www.test.org/path/xmi'

    assert uri.apply_relative_from_me('../mypath') == 'http://www.test.org/mypath'
    assert uri.apply_relative_from_me('../../mypath') == 'http://www.test.org/mypath'


def test_resourceset_default_decoders():
    rset = ResourceSet()
    assert 'xmi' in rset.resource_factory
    assert 'ecore' in rset.resource_factory
    assert '*' in rset.resource_factory
    assert rset.resource_factory is not ResourceSet.resource_factory


def test_resourceset_createresource_simple():
    rset = ResourceSet()
    resource = rset.create_resource(URI('simpleuri'))
    rpath = path.abspath('simpleuri')
    assert rpath in rset.resources
    assert rset.resources[rpath] is resource
    assert rset in resource.decoders
    assert isinstance(resource, rset.resource_factory['*']('').__class__)


def test_resourceset_createresource_ecore():
    rset = ResourceSet()
    resource = rset.create_resource(URI('simple.ecore'))
    rpath = path.abspath('simple.ecore')
    assert rpath in rset.resources
    assert rset.resources[rpath] is resource
    assert rset in resource.decoders
    assert isinstance(resource, rset.resource_factory['ecore']('').__class__)


def test_resourceset_createresource_xmi():
    rset = ResourceSet()
    resource = rset.create_resource(URI('simple.xmi'))
    rpath = path.abspath('simple.xmi')
    assert rpath in rset.resources
    assert rset.resources[rpath] is resource
    assert rset in resource.decoders
    assert isinstance(resource, rset.resource_factory['xmi']('').__class__)


def test_resourceset_canresolve():
    rset = ResourceSet()
    assert rset.can_resolve('http://simple.ecore#//test') is False
    rset.create_resource(URI('http://simple.ecore'))
    assert rset.can_resolve('http://simple.ecore#//test') is True


def test_globaluridecoder():
    assert Global_URI_decoder.can_resolve('http://simple.ecore'
                                          '#//test') is False
    rset = ResourceSet()
    resource = rset.create_resource('http://simple.ecore')
    global_registry['http://simple.ecore'] = resource
    assert Global_URI_decoder.can_resolve('http://simple.ecore#//test') is True


def test_resource_load_proxy_missinghref(simplemm):
    rset = ResourceSet()
    rset.metamodel_registry[simplemm.nsURI] = simplemm
    root = rset.get_resource(path.join('tests', 'xmi',
                                       'xmi-tests', 'a1-1.xmi')).contents[0]
    assert isinstance(root.a[0].tob[0], EProxy)
    with pytest.raises(TypeError):
        root.a[0].tob[0].eClass


def test_resource_load_proxy_href(simplemm):
    rset = ResourceSet()
    rset.metamodel_registry[simplemm.nsURI] = simplemm
    root = rset.get_resource(path.join('tests', 'xmi',
                                       'xmi-tests', 'a1.xmi')).contents[0]
    rset.get_resource(path.join('tests', 'xmi', 'xmi-tests', 'b1.xmi'))
    assert isinstance(root.a[0].tob[0], EProxy)
    B = simplemm.getEClassifier('B')
    root.a[0].tob[0].eClass  # We force the proxy resolution
    assert isinstance(root.a[0].tob[0], B.python_class)
    assert EcoreUtils.isinstance(root.a[0].tob[0], B)


def test_resource_load_proxy_href_inner(simplemm):
    rset = ResourceSet()
    rset.metamodel_registry[simplemm.nsURI] = simplemm
    root = rset.get_resource(path.join('tests', 'xmi',
                                       'xmi-tests', 'a2.xmi')).contents[0]
    rset.get_resource(path.join('tests', 'xmi', 'xmi-tests',
                                'inner', 'b2.xmi'))
    assert isinstance(root.a[0].tob[0], EProxy)
    B = simplemm.getEClassifier('B')
    root.a[0].tob[0].eClass  # We force the proxy resolution
    assert isinstance(root.a[0].tob[0], B.python_class)
    assert EcoreUtils.isinstance(root.a[0].tob[0], B)


def test_resource_load_proxy_href_force_resolve(simplemm):
    rset = ResourceSet()
    rset.metamodel_registry[simplemm.nsURI] = simplemm
    root = rset.get_resource(path.join('tests', 'xmi',
                                       'xmi-tests', 'a2.xmi')).contents[0]
    rset.get_resource(path.join('tests', 'xmi', 'xmi-tests',
                                'inner', 'b2.xmi'))
    assert isinstance(root.a[0].tob[0], EProxy)
    B = simplemm.getEClassifier('B')
    root.a[0].tob[0].force_resolve()  # We force the proxy resolution
    assert isinstance(root.a[0].tob[0], B.python_class)
    assert EcoreUtils.isinstance(root.a[0].tob[0], B)


def test_resource_load_proxy_href_force_resolve_idempotent(simplemm):
    rset = ResourceSet()
    rset.metamodel_registry[simplemm.nsURI] = simplemm
    root = rset.get_resource(path.join('tests', 'xmi',
                                       'xmi-tests', 'a2.xmi')).contents[0]
    rset.get_resource(path.join('tests', 'xmi', 'xmi-tests',
                                'inner', 'b2.xmi'))
    x = root.a[0].tob[0]
    x.force_resolve()
    wrapped = x._wrapped
    x.force_resolve()
    assert wrapped is x._wrapped


def test_resource_mmregistry_isolation():
    global_registry['cdef'] = None
    rset1 = ResourceSet()
    rset2 = ResourceSet()
    rset1.metamodel_registry['abcd'] = None
    assert 'abcd' not in rset2.metamodel_registry
    assert 'cdef' in rset2.metamodel_registry
    assert 'cdef' in rset1.metamodel_registry


def test_resource_double_load(simplemm):
    rset = ResourceSet()
    rset.metamodel_registry[simplemm.nsURI] = simplemm
    root = rset.get_resource(path.join('tests', 'xmi',
                                       'xmi-tests', 'a1.xmi')).contents[0]
    root2 = rset.get_resource(path.join('tests', 'xmi',
                                        'xmi-tests', 'a1.xmi')).contents[0]
    assert root is root2


def test_resource_swap(simplemm):
    root = simplemm.Root()
    a = simplemm.A()
    b = simplemm.B()
    root.a.append(a)
    root.b.append(b)

    r1 = XMIResource(URI('resource1.xmi'))
    r2 = XMIResource(URI('resource2.xmi'))
    r1.append(root)

    assert root.eResource is r1
    assert a.eResource is root.eResource
    assert b.eResource is root.eResource

    r2.append(root)
    assert root.eResource is r2
    assert a.eResource is root.eResource
    assert b.eResource is root.eResource


def test_resource_multiroot_urifragment():
    A = EClass('A')
    A.eStructuralFeatures.append(EReference('toa', A, containment=True))

    a1 = A()
    a2 = A()
    a3 = A()
    a2.toa = a3

    resource = XMIResource('test')
    resource.append(a1)
    resource.append(a2)

    assert a1.eURIFragment() == '/0'
    assert a2.eURIFragment() == '/1'
    assert a3.eURIFragment() == '/1/@toa'

    resource.remove(a2)
    assert len(resource.contents) == 1
    assert a2._eresource is None


def test_resource_multiroot_container_changement():
    resource = XMIResource('testResource')
    A = EClass('A')
    A.eStructuralFeatures.append(EReference('toa', A, containment=True))

    a1 = A()
    a2 = A()

    resource = XMIResource('test')
    resource.append(a1)
    resource.append(a2)

    assert resource.contents == [a1, a2]

    a1.toa = a2
    assert resource.contents == [a1]


def test_resource_extract_rootnum_and_frag():
    num, frag = Resource.extract_rootnum_and_frag('/1/a.b')
    assert num == 1
    assert frag == '/a.b'

    num, frag = Resource.extract_rootnum_and_frag('/123')
    assert num == 123
    assert frag == ''

    num, frag = Resource.extract_rootnum_and_frag('/234/a/b/c/d')
    assert num == 234
    assert frag == '/a/b/c/d'


def test_resource_update_URI():
    resource = Resource(uri=URI('test_uri'))
    assert resource.uri.plain == 'test_uri'

    resource.uri = URI('http://new_URI')
    assert resource.uri.plain == 'http://new_URI'

    resource.uri = 'http://newnewURI'
    assert resource.uri.plain == 'http://newnewURI'

    rset = ResourceSet()
    resource = rset.create_resource('http://test_URI')
    assert resource.uri.plain == 'http://test_URI'

    resource.uri = 'http://newURI'
    assert 'http://newURI' in rset.resources
    assert 'http://test_URI' not in rset.resources
    assert resource.uri.plain == 'http://newURI'


def test_resource_normalize_unknown_protocol():
    u = URI('pathmap://test')
    assert u.normalize() == u.plain

    u = URI('platform:/test')
    assert u.normalize() == u.plain


def test_resource_normalize_change_protocol():
    r = Resource(path.join('..', 'test'))
    r.uri = 'pathmap://test'

    assert r.uri.normalize() == r.uri.plain
    assert r.uri.plain == 'pathmap://test'


def test_resource_normalize_with_protocol():
    u1 = URI('test/toto.xmi')
    u2 = URI('pathmap://UML_METAMODELS/UML.metamodel.uml')

    assert u1.relative_from_me(u2) == u2.plain


def test__resource_uriconverter_abstract():
    a = AbstractURIConverter()
    u = URI('test')

    with pytest.raises(NotImplementedError):
        a.convert(u)

    with pytest.raises(NotImplementedError):
        a.can_handle(u)


def test__resource_uriconverter_simple():
    class MyURI(URI):
        pass

    class MyURIConverter(AbstractURIConverter):
        @staticmethod
        def can_handle(uri):
            return uri.protocol == 'myuri'

        @staticmethod
        def convert(uri):
            new_path = uri.plain.replace('myuri://', '')
            return MyURI(new_path)

    rset = ResourceSet()
    rset.uri_converter.append(MyURIConverter)

    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'C.ecore')
    resource = rset.get_resource(xmi_file)
    root = resource.contents[0]
    assert root.eClassifiers[0]
    assert root.eClassifiers[0].eStructuralFeatures[0].eType.name == 'SuperStuff'


def test__resource_change_container(simplemm):
    a = simplemm.A()
    root = simplemm.Root()

    r = Resource(path.join('..', 'test', 'toto.xmi'))
    r.append(a)
    r.append(root)

    assert len(r.contents) == 2
    assert len(root.a) == 0

    root.a.append(a)
    assert len(root.a) == 1
    assert root.a == [a]
    assert len(r.contents) == 1

    r.append(a)
    assert len(root.a) == 0
    assert len(r.contents) == 2
