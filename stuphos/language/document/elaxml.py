# This is more like ela to YAML/JSON.
from xml.dom.minidom import parseString, Text
import op # for nling, indent

defaultValue = object()

TEXT_REPR_NS = 'text-repr'


class configurableTranslator:
    OVERRIDDABLE_ATTRIBUTES = \
        ['attr_format', 'nsAttr_format', 'docName_default',
         'childrenSeq_name', 'elem_name', 'nsAttrs_name',
         'attrs_name']

    def __init__(self, **kwd):
        self.__dict__.update \
            (dict(nv for nv in kwd.items() if nv[0]
             in self.OVERRIDDABLE_ATTRIBUTES))


    cmdlnOptions = None

    def getOption(self, name, default = None):
        return getattr(self.cmdlnOptions, name, default)

    def getConfigOption(self, name, default = None):
        r = self.getOption(name, defaultValue)
        if r is defaultValue:
            return getattr(self, name, default)

        return r


class baseTranslator:
    reprStringValue = reprValue = repr # json.dumps

    attr_format = nsAttr_format = '{name}: {reprValue}'

    docName_default = 'document' # (elaxml$doc)'
    childrenSeq_name = 'children' # (elaxml$children)'
    elem_name = 'name'

    nsAttrs_name = 'nsAttrs$'
    attrs_name = 'attributes$'


    def translate(self, source, name = defaultValue, **kwd):
        if isinstance(source, str):
            source = self.parseString(source) 

        if name is defaultValue:
            name = self.docName_default

        return self.documentVisit(source, **kwd) \
               if name is None else self.documentVisitNamed \
                    (name, source, **kwd)

    class loadContext:
        def __init__(self, parent = None, node = None, nsAttrs = None):
            self.parent = parent
            self.ns = dict() if nsAttrs is None else nsAttrs
            self.node = node

        def subContext(self, node, **kwd):
            return self.subContextClass(parent = self, node = node, **kwd)


        # Common option interpretations.
        def isTextRepr(self, node):
            try: return self.ns['xmlns$'] == TEXT_REPR_NS
            except KeyError:
                return self.parent.isTextRepr(node)


    class childContext(loadContext):
        pass # could make mandate parent
    childContext.subContextClass = childContext

    class parentContext(loadContext):
        pass
    parentContext.subContextClass = childContext


    def documentVisit(self, doc, context = None):
        if context is None:
            context = self.parentContext()

        return self.visitChildNodes(doc.childNodes, context)


    # Mid-level:
    def loadNSAttrs(self, attrs):
        return dict(self.loadNSAttrsMultiple \
            (attrs.items() if attrs else ()))

    def loadNSAttrsMultiple(self, items):
        for (name, value) in items:
            if name == 'xmlns':
                yield ('xmlns$', value)

            elif name.startswith('xmlns:'):
                yield (name[6:], value)

    def nonNSAttrs(self, items):
        for (name, value) in items:
            if name != 'xmlns' and not name.startswith('xmlns:'):
                yield (name, value)


    def visitNodeSelective(self, node, context):
        # todo: opportunity to differentiate between text nodes and elements.
        if self.isTextNode(node):
            return self.visitTextNode(node, context)

        return self.visitNode(node, context)


    def isTextRepr(self, node, context):
        return self.getConfigOption('text_repr')


    def nodeAttrImpl(self, format, name, value, context):
        return format.format \
            (name = name, value = value,
             reprValue = self.reprStringValue \
                (value))

    def nodeNSAttr(self, name, value, context):
        return self.nodeAttrImpl(self.nsAttr_format, name, value, context)
    def nodeAttr(self, name, value, context):
        return self.nodeAttrImpl(self.attr_format, name, value, context)


class providedTranslator(configurableTranslator, baseTranslator):
    '''
    components:
        elaxml:
            code::
                def api$():
                    return 'kernel/lookup$'('stuphos.language.document.elaxml')

                def translator():
                    return act(api$().translator, args$(), keywords$())
                def htmlToXml():
                    return act(api$().htmlToXml, args$(), keywords$())

            interfaces:
                views::
                    translate(view):
                        context(trigger)::
                            if request.method == 'POST':
                                p = request.POST
                                xml = p['xml']
                            else:
                                p = request.GET
                                xml = p.get('xml')

                            if is$not$none(xml):
                                elaxml = call.assets.Itham.components.elaxml.code
                                initialize(elaxml)

                                if p.get('convert'):
                                    xml = elaxml.htmlToXml(xml)

                                xml = elaxml.translator() \
                                    .translate(xml)

                                # 'kernel/info'(string(xml).substring(0, 60))

                                # return xml
                                context['output'] = xml
                                context['format'] = request.method == 'POST'


                        template::
                            {% if not format and output %}{{ output|safe }}{% else %}
                            <style type="text/css">
                            .input, .output { width: 98%; height: 86%; }
                            </style>

                            {% if format %}
                            <textarea class="output">{{ output }}</textarea>
                            {% else %}
                            <form method="POST">
                                <textarea class="input" name="xml"></textarea><br />
                                <input type="checkbox" name="convert">Convert to XML
                                <input type="submit">
                                </form>
                            {% endif %}
                            {% endif %}

                        usage::
                            components/elaxml/views/translate?xml=

    '''


class baseXmlToStringTranslator:
    # Toplevel:
    parseString = staticmethod(parseString)
    TextNodeClass = Text


    def isTextNode(self, node):
        return isinstance(node, self.TextNodeClass)

    @nling
    def documentVisitNamed(self, name, doc, **kwd):
        yield f'{name}:'
        yield indent(self.documentVisit(doc, **kwd))


    @nling
    def visitChildNodes(self, children, context, **kwd):
        # Erm, how do we represent an anonymous sequence..?
        # YAML.

        if children: # todo: might this be generator/iterator?
            yield f'{kwd.get("ofMap") and "  " or ""}{self.childrenSeq_name}:'

            for sub in children:
                yield indent(self.visitNodeSelective(sub, context))
                yield ''


    @nling
    def visitTextNode(self, node, context):
        # todo: context.ns flags or maybe parental node/context flags
        # for output formatting style.
        # yield '- <'
        if self.isTextRepr(node, context):
            yield '- ' + self.reprStringValue(node.data)
        else:
            yield '- |'
            yield indent(node.data.lstrip())


    @nling
    def visitNode(self, node, context):
        # Collect namespace into context.
        nsAttrs = self.loadNSAttrs(node.attributes)
        if nsAttrs:
            context = context.subContext(self, nsAttrs = nsAttrs)

        yield '- {elem_name}: {name}'.format \
            (elem_name = self.elem_name,
             name = node.localName)

        yield self.visitNodeInterior \
                (node.attributes,
                 node.childNodes,
                 context)


    @nling
    def renderNodeAttrs(self, name, attrs, render, context):
        yield f'  {name}:'

        for (name, value) in attrs:
            yield indent(render(name, value, context))


    @nling
    def visitNodeInterior(self, attrs, children, context):
        # (pre-parsed)
        if context.ns:
            yield self.renderNodeAttrs \
                (self.nsAttrs_name, context.ns.items(),
                 self.nodeNSAttr, context)

            yield ''

        attrs = dict(self.nonNSAttrs(attrs.items())) if attrs else False
        if attrs:
            yield self.renderNodeAttrs \
                (self.attrs_name, attrs.items(),
                 self.nodeAttr, context)

            yield ''

        yield self.visitChildNodes(children, context, ofMap = True)


class baseXmlToSerializationTranslator(baseXmlToStringTranslator):
    def documentVisitNamed(self, name, doc, **kwd):
        return dict(document = self.documentVisit(doc, **kwd),
                    name = name)


    def visitChildNodes(self, children, context, **kwd):
        # Erm, how do we represent an anonymous sequence..?
        # YAML.

        return {self.childrenSeq_name:
                list(self.visitNodeSelective \
                    (sub, context) for sub in children)}


    def visitTextNode(self, node, context):
        return node.data


    def visitNode(self, node, context):
        # Collect namespace into context.
        nsAttrs = self.loadNSAttrs(node.attributes)
        if nsAttrs:
            context = context.subContext(self, nsAttrs = nsAttrs)

        r = self.visitNodeInterior \
                (node.attributes,
                 node.childNodes,
                 context)

        r[self.elem_name] = node.localName

        return r


    def renderNodeAttrs(self, name, attrs, render, context):
        yield (name, list(render(name, value, context)
                          for (name, value) in attrs))


    def visitNodeInterior(self, attrs, children, context):
        # (pre-parsed)
        r = dict()

        if context.ns:
            r.update(self.renderNodeAttrs \
                (self.nsAttrs_name, context.ns.items(),
                 self.nodeNSAttr, context))

        attrs = dict(self.nonNSAttrs(attrs.items())) if attrs else False
        if attrs:
            r.update(self.renderNodeAttrs \
                (self.attrs_name, attrs.items(),
                 self.nodeAttr, context))

        r.update(self.visitChildNodes(children, context)) # , ofMap = True))

        return r


class xmlTranslator(baseXmlToStringTranslator, providedTranslator):
    pass

class xmlToSerializationTranslator(baseXmlToSerializationTranslator, providedTranslator):
    pass


translator = xmlTranslator
defaultTranslator = translator()


def transform(options, data):
    if options.json:
        from json import dumps

        if isinstance(data, str):
            from yaml import safe_load as loads
            data = loads(data)

        return dumps(data, indent = 1)

    return data

def internalizeValue(value):
    if value.isdigit():
        return int(value)
    if value.lower() in ['true', 'yes', 'on']:
        return True
    if value.lower() in ['false', 'no', 'off']:
        return False
    if value.lower() in ['none', 'nil', 'null']:
        return None

    return value

def paramLoad(input):
    return dict((name, internalizeValue(value))
                for (name, value) in
                (p.split('=', 1) for p in input))

def rewriteTextShould(text):
    # if text.strip():
    #   print(text.__class__.__name__)
    #   import pdb; pdb.set_trace()

    if '<' in text or '>' in text:
        return text

def rewriteIntoCDATAs(tag):
    from bs4 import CData #, Stylesheet

    # def findStylesheet(n):
    #   print(n.__class__.__name__)

    # XXX findAll(string = True) doesn't get NavigableStrings..?!
    for n in tag.findAll(string = True):
    # for n in tag.findAll(findStylesheet):
        # print(n.__class__.__name__)
        # if isinstance(n, Stylesheet):
        #   import pdb; pdb.set_trace()

        t = str(n) # n.text

        t = rewriteTextShould(t)
        if t:
            n.insert_before(CData(t))
            n.extract()

    return tag

def htmlToXml(data):
    # Convert to XML/XHTML
    from bs4 import BeautifulSoup as BS
    # data = BS(data, ['xml', 'fast']).decode()
    data = BS(data)

    # Breaks basically around here (in a style tag)
    # .vector-icon.mw-ui-icon-wikimedia-speechBubbleAdd{background-image:url(/w/load.php?modules=skins.vector.icons.js&image=
    # So, could transform all text nodes to be CDATAs?!
    data = rewriteIntoCDATAs(data)

    # data.is_xml = True
    return data.decode()


def main(argv = None):
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('--html', action = 'store_true')
    parser.add_option('--json', action = 'store_true')
    parser.add_option('-p', '--parameter', action = 'append', default = [])
    parser.add_option('--no-translate', action = 'store_true')
    parser.add_option('--translator')
    (options, args) = parser.parse_args(argv)

    if len(args) < 3:
        if len(args):
            input = open(args[0])

            if len(args) == 2:
                output = open(args[1], 'w+')
            else:
                from sys import stdout as output
        else:
            from sys import stdin as input
            from sys import stdout as output
    else:
        raise 'too many arguments'


    data = input.read()

    if options.html:
        data = htmlToXml(data)

        if options.no_translate:
            output.write(data)
            return


    if options.translator == 'serialization':
        translatorClass = xmlToSerializationTranslator
    else:
        translatorClass = translator

    p = paramLoad(options.parameter)
    if p:
        t = translatorClass(**p, cmdlnOptions = options)
    elif options.translator:
        t = translatorClass()
    else:
        t = defaultTranslator

    data = t.translate(data)
    data = transform(options, data)
    output.write(data)

if __name__ == '__main__':
    main()
