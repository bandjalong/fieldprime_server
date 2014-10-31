#
# models.py
# Michael Kirk 2013
#
# Sqlalchemy models for the database.
#
# The models were originally autogenerated by sqlautocode
#

__all__ = ['Trial', 'Node', 'Attribute', 'AttributeValue', 'Datum', 'Trait']


#import sqlalchemy
from sqlalchemy import *
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, relationship, sessionmaker, Session
from const import *
import util
from functools import wraps

### sqlalchemy CONSTANTS: ######################################################################

DeclarativeBase = declarative_base()
metadata = DeclarativeBase.metadata

attributeValue = Table(unicode(TABLE_ATTRIBUTE_VALUES), metadata,
    Column(u'nodeAttribute_id', INTEGER(), ForeignKey('nodeAttribute.id'), primary_key=True, nullable=False),
    Column(u'node_id', INTEGER(), ForeignKey('node.id'), primary_key=True, nullable=False),
    Column(unicode(AV_VALUE), TEXT(), nullable=False),
)

datum = Table(u'datum', metadata,
    Column(u'node_id', INTEGER(), ForeignKey('node.id'), primary_key=True, nullable=False),
    Column(u'traitInstance_id', INTEGER(), ForeignKey('traitInstance.id'), nullable=False),
    Column(u'timestamp', BigInteger(), primary_key=True, nullable=False),
    Column(u'gps_long', Float(asdecimal=True)),
    Column(u'gps_lat', Float(asdecimal=True)),
    Column(u'userid', TEXT()),
    #Column(u'notes', TEXT()),
    Column(u'numValue', DECIMAL(precision=11, scale=3)),
    Column(u'txtValue', TEXT()),
)

traitInstance = Table(u'traitInstance', metadata,
    Column(u'id', INTEGER(), primary_key=True, nullable=False),
    Column(u'trial_id', INTEGER(), ForeignKey('trial.id'), nullable=False),
    Column(u'trait_id', INTEGER(), ForeignKey('trait.id'), nullable=False),
    Column(u'dayCreated', INTEGER(), nullable=False),
    Column(u'seqNum', INTEGER(), nullable=False),
    Column(u'sampleNum', INTEGER(), nullable=False),
    Column(u'token', VARCHAR(length=31), nullable=False),
)

trialTrait = Table(u'trialTrait', metadata,
    Column(u'trial_id', INTEGER(), ForeignKey('trial.id'), primary_key=True, nullable=False),
    Column(u'trait_id', INTEGER(), ForeignKey('trait.id'), primary_key=True, nullable=False),
    Column(u'barcodeAtt_id', INTEGER(), ForeignKey('nodeAttribute.id'), nullable=True)
)


### sqlalchemy CLASSES: ######################################################################

class TrialTrait(DeclarativeBase):
    __table__ = trialTrait
    #relation definitions:
    barcodeAtt = relation('NodeAttribute', primaryjoin='TrialTrait.barcodeAtt_id==NodeAttribute.id')

class AttributeValue(DeclarativeBase):
    __table__ = attributeValue

    #relation definitions
    nodeAttribute = relation('NodeAttribute', primaryjoin='AttributeValue.nodeAttribute_id==NodeAttribute.id')
    node = relation('Node', primaryjoin='AttributeValue.node_id==Node.id')

    def setValueWithTypeUpdate(self, newVal):
    # Set the value, and if the val is not an integer, set the type to text.
    # NB by default datatypes are integer, if necessary fall back to decimal,
    # and then to string
        self.value = newVal
        if not self.nodeAttribute.datatype == T_STRING and not util.isInt(newVal):
            self.nodeAttribute.datatype = T_DECIMAL if util.isNumeric(newVal) else T_STRING


class Datum(DeclarativeBase):
    __table__ = datum

    #relation definitions
    node = relation('Node', primaryjoin='Datum.node_id==Node.id')
    traitInstance = relation('TraitInstance', primaryjoin='Datum.traitInstance_id==TraitInstance.id')

    @staticmethod
    def valueFieldName(traitType):
        if (traitType == T_INTEGER or
            traitType == T_DECIMAL or
            traitType == T_CATEGORICAL or
            traitType == T_DATE):
            return 'numValue'
        else:
            # traitType == T_STRING
            # traitType == T_PHOTO
            return 'txtValue'

    def isNA(self):
        return self.txtValue is None and self.numValue is None

    def getValue(self):
    #------------------------------------------------------------------
    # Return a value, how the value is stored/represented is type specific.
    # NB if the database value is null, then "NA" is returned.
        type = self.traitInstance.trait.type
        value = '?'
        if type == T_INTEGER: value = self.numValue
        elif type == T_DECIMAL: value = self.numValue
        elif type == T_STRING: value = self.txtValue
        elif type == T_CATEGORICAL:
            value = self.numValue
            # Need to look up the text for the value:
            if value is not None:
                session = Session.object_session(self)
                traitId = self.traitInstance.trait.id
                trtCat = session.query(TraitCategory).filter(
                    and_(TraitCategory.trait_id == traitId, TraitCategory.value == value)).one()
                value = trtCat.caption
        elif type == T_DATE: value = self.numValue
        elif type == T_PHOTO:
#             session = Session.object_session(self)
#             traitId = self.traitInstance.trait.id
#             nodeId = self.node.id
#             trialId = self.node.trial_id
#             value = photoFileName(dbusername, trialId, traitId, nodeId, token, seqNum, sampNum, fileExtension):
            value = self.txtValue

            #MFK return link to photo.
        #if type ==     T_LOCATION: value = d.txtValue

        # Convert None to "NA"
        if value is None:
            value = "NA"
        return value

class Trait(DeclarativeBase):
    __tablename__ = 'trait'
    __table_args__ = {}

    #column definitions
    caption = Column(u'caption', VARCHAR(length=63), nullable=False)
    description = Column(u'description', TEXT(), nullable=False)
    id = Column(u'id', INTEGER(), primary_key=True, nullable=False)
    sysType = Column(u'sysType', INTEGER(), nullable=False)
    type = Column(u'type', INTEGER(), nullable=False)

    #relation definitions
    trials = relation('Trial', primaryjoin='Trait.id==trialTrait.c.trait_id', secondary=trialTrait, secondaryjoin='trialTrait.c.trial_id==Trial.id')
    categories = relation('TraitCategory')    # NB, only relevant for Categorical type


class TraitCategory(DeclarativeBase):
    __tablename__ = 'traitCategory'
    __table_args__ = {}

    #column definitions
    caption = Column(u'caption', TEXT(), nullable=False)
    imageURL = Column(u'imageURL', TEXT())
    trait_id = Column(u'trait_id', INTEGER(), ForeignKey('trait.id'), primary_key=True, nullable=False)
    value = Column(u'value', INTEGER(), primary_key=True, nullable=False)

    #relation definitions
    trait = relation('Trait', primaryjoin='TraitCategory.trait_id==Trait.id')

    @staticmethod
    def getCategoricalTraitValue2NameMap(dbc, traitId):
    # Return dictionary providing value to caption map for specified trait.
    # The trait should be categorical, if not empty map will be returned, I think.
        cats = dbc.query(TraitCategory).filter(TraitCategory.trait_id == traitId).all()
        util.flog('num cats: {0}'.format(len(cats)))
        retMap = {}
        for cat in cats:
            retMap[cat.value] = cat.caption
        return retMap


class TraitInstance(DeclarativeBase):
    __table__ = traitInstance

    #relation definitions
    trait = relation('Trait', primaryjoin='TraitInstance.trait_id==Trait.id')
    trial = relation('Trial', primaryjoin='TraitInstance.trial_id==Trial.id')
    nodes = relation('Node', primaryjoin='TraitInstance.id==Datum.traitInstance_id', secondary=datum, secondaryjoin='Datum.node_id==Node.id')

    def getDeviceId(self):
        return self.token.split('.')[0]
    def getDownloadTime(self):
        return self.token.split('.')[1]
    def numData(self):
        session = Session.object_session(self)
        count = session.query(Datum).filter(Datum.traitInstance_id == self.id).count()
        return count


# class TrialTraitNumeric
# Validation information specific to a given trial/trait.
class TrialTraitNumeric(DeclarativeBase):
    __tablename__ = 'trialTraitNumeric'
    max = Column(u'max', DECIMAL(precision=18, scale=9))
    min = Column(u'min', DECIMAL(precision=18, scale=9))
    cond = Column(u'validation', TEXT())
    trait_id = Column(u'trait_id', INTEGER(), ForeignKey('trait.id'), primary_key=True, nullable=False)
    trial_id = Column(u'trial_id', INTEGER(), ForeignKey('trial.id'), primary_key=True, nullable=False)
    def getMin(self):
        return None if self.min is None else self.min.normalize()   # stripped of unnecessary zeroes
    def getMax(self):
        return None if self.max is None else self.max.normalize()

# class TraitString
# Validation information specific to a given trial/trait.
class TraitString(DeclarativeBase):
    __tablename__ = 'traitString'
    trait_id = Column(u'trait_id', INTEGER(), ForeignKey('trait.id'), primary_key=True, nullable=False)
    trial_id = Column(u'trial_id', INTEGER(), ForeignKey('trial.id'), primary_key=True, nullable=False)
    pattern = Column(u'pattern', TEXT())


#
# class ScoreSet
# NOT a database class, but a container for a set of traitInstances that
# make up a scoreSet
#
class ScoreSet:
    def __init__(self, trait_id, seqNum, token):
        self.trait_id = trait_id
        self.seqNum = seqNum
        self.token = token
        self.instances = []
    def addInstance(self, ti):
        self.instances.append(ti)
    def getInstances(self):
        return self.instances


class Trial(DeclarativeBase):
    __tablename__ = 'trial'
    __table_args__ = {}

    #column definitions:
    acronym = Column(u'acronym', TEXT())
    id = Column(u'id', INTEGER(), primary_key=True, nullable=False)
    name = Column(u'name', VARCHAR(length=63), nullable=False)
    site = Column(u'site', TEXT())
    year = Column(u'year', TEXT())

    #relation definitions:
    traits = relation('Trait', primaryjoin='Trial.id==trialTrait.c.trial_id', secondary=trialTrait, secondaryjoin='trialTrait.c.trait_id==Trait.id')
    tuAttributes = relationship('NodeAttribute')
    nodes = relationship('Node')
    trialProperties = relationship('TrialProperty')

    def addOrGetNode(self, row, col):
        try:
            session = Session.object_session(self)
            tu = session.query(Node).filter(and_(Node.trial_id == self.id, Node.row == row,
                                                      Node.col == col)).one()
        except sqlalchemy.orm.exc.NoResultFound:
            tu = Node()
            tu.row = row
            tu.col = col
            tu.trial_id = self.id
            session.add(tu)
            session.commit()
        except sqlalchemy.orm.exc.MultipleResultsFound:
            return None

        return tu

    def numScores(self):
        tis = self.getTraitInstances()
        count = 0
        for ti in tis:
            count += ti.numData()
        return count

    def numScoreSets(self):
        ss = self.getScoreSets()
        return len(ss)

    def getTraitInstances(self):
    #-----------------------------------------------------------------------
    # Return all the traitInstances for this trial, ordered by trait, token, seqnum,
    # dayCreate, samplenum. So traitInstances in the same scoreSet are contiguous.
    # NB sorting by dayCreated shouldn't be necessary, but is temporarily needed
    # - see comment on getScoreSets().
        session = Session.object_session(self)
        return session.query(TraitInstance).filter(
            TraitInstance.trial_id == self.id).order_by(
            TraitInstance.trait_id, TraitInstance.token, TraitInstance.seqNum,
            TraitInstance.dayCreated, TraitInstance.sampleNum).all()

    def getScoreSets(self):
    #----------------------------------------------------------------------------------------------------
    # Returns list of ScoreSets for this trial.
    # NB the use of dayCreated in the comparison shouldn't be necessary, but it is at the moment
    # for a fix we have for a bug in the app where a scoreset made after deleting a scoreset (of the
    # same trait) could cause an overwrite of the first scoreset on the server. This now fixed,
    # but using dayCreated catches most instances of this. When all clients are upgraded, this
    # can go.
        scoreSets = []
        tiList = self.getTraitInstances()
        lastSeqNum = -1
        lastTraitId = -1
        lastToken = 'x'
        lastDayCreated = -1
        for ti in tiList:   # Note we have assumptions about ordering in tiList here
            traitId = ti.trait_id
            seqNum = ti.seqNum
            token = ti.token
            dayCreated = ti.dayCreated
            if seqNum != lastSeqNum or traitId != lastTraitId or token != lastToken or dayCreated != lastDayCreated:
                # First ti in a new scoreSet, create and add the ScoreSet:
                nss = ScoreSet(traitId, seqNum, token)
                scoreSets.append(nss)
            nss.addInstance(ti)
            lastSeqNum = seqNum
            lastTraitId = traitId
            lastToken = token
        return scoreSets

def oneException2None(func):
#--------------------------------------------------------------------
# Decorator used for sqlalchemy one() queries, which throw exceptions if
# there isn't exactly one result. This function traps the exceptions, it
# returns the result if exactly one is found, else None.
#
    @wraps(func)
    def with_traps(*args, **kwargs):
        try:
            ret = func(*args, **kwargs)
        except sqlalchemy.orm.exc.NoResultFound:
            return None
        except sqlalchemy.orm.exc.MultipleResultsFound:
            return None
        return ret
    return with_traps


#
# TrialProperty
# Table for trial attributes.
# NB: what attributes are available to be set are hard-coded into the software.
# Users may change the values of the hardcoded set, but not create new attributes.
# Note also that the app web service will sent whatever is in this table (regardless)
# of what the admin web service currently supports.
# The values in the table are text, but the real types, as presented to the user, could
# be boolean, categorical, numeric etc. They are to be sent to the app via json however
# so must map to some text representation anyway. We could perhaps give them a type, where
# the types are those supported by json. But for them to be of use on the app, the app
# code must know the type anyway.
# Anyway, if we added tables to list the supported types, then the admin interface at least
# could be driven from the tables, and to add a new attribute we would only need adjust
# the tables. But we don't have that attow. On the other hand, a table hardcoded in the
# software isn't necessarily any harder to adjust.
# MFK - would be better named TrialProperty
class TrialProperty(DeclarativeBase):
    __tablename__ = 'trialProperty'
    __table_args__ = {}

    #column definitions:
    trial_id = Column(u'trial_id', INTEGER(), ForeignKey('trial.id'), primary_key=True, nullable=False)
    name = Column(u'name', TEXT(), primary_key=True)
    value = Column(u'value', TEXT())

    def __init__(self, tid, name, value):
        self.trial_id = tid
        self.name = name
        self.value = value

    @staticmethod
    @oneException2None
    def getPropertyValue(dbc, trialId, propName):
    # Return dictionary providing value to caption map for specified trait.
    # The trait should be categorical, if not empty map will be returned, I think.
        return dbc.query(TrialProperty).filter(
                and_(TrialProperty.trial_id == trialId, TrialProperty.name == propName)
                ).one().value


class Node(DeclarativeBase):
    __tablename__ = 'node'
    __table_args__ = {}

    #column definitions
    barcode = Column(u'barcode', TEXT())
    col = Column(u'col', INTEGER(), nullable=False)
    description = Column(u'description', TEXT())
    id = Column(u'id', INTEGER(), primary_key=True, nullable=False)
    row = Column(u'row', INTEGER(), nullable=False)
    trial_id = Column(u'trial_id', INTEGER(), ForeignKey('trial.id'), nullable=False)
    longitude = Column(u'longitude', Float(asdecimal=False))
    latitude = Column(u'latitude', Float(asdecimal=False))

    #relation definitions
    trial = relation('Trial', primaryjoin='Node.trial_id==Trial.id')
    nodeAttributes = relation('NodeAttribute', primaryjoin='Node.id==AttributeValue.node_id',
                                   secondary=attributeValue, secondaryjoin='AttributeValue.nodeAttribute_id==NodeAttribute.id')
    traitInstances = relation('TraitInstance', primaryjoin='Node.id==Datum.node_id', secondary=datum, secondaryjoin='Datum.traitInstance_id==TraitInstance.id')
    attVals = relation('AttributeValue')

class NodeAttribute(DeclarativeBase):
    __tablename__ = 'nodeAttribute'
    __table_args__ = {}

    #column definitions
    id = Column(u'id', INTEGER(), primary_key=True, nullable=False)
    name = Column(u'name', VARCHAR(length=31), nullable=False)
    trial_id = Column(u'trial_id', INTEGER(), ForeignKey('trial.id'), nullable=False)
    datatype = Column(unicode(TUA_DATATYPE), INTEGER(), default=T_INTEGER, nullable=False)
    func = Column(unicode(TUA_FUNC), INTEGER(), default=0, nullable=False)

    #relation definitions
    trial = relation('Trial', primaryjoin='NodeAttribute.trial_id==Trial.id')
    nodes = relation('Node', primaryjoin='NodeAttribute.id==AttributeValue.nodeAttribute_id', secondary=attributeValue, secondaryjoin='AttributeValue.node_id==Node.id')

class System(DeclarativeBase):
    __tablename__ = 'system'
    __table_args__ = {}
    name = Column(u'name', VARCHAR(length=63), primary_key=True, nullable=False)
    value = Column(u'value', VARCHAR(length=255), nullable=True)
    def __init__(self, name, value):
        self.name = name
        self.value = value

class NodeNote(DeclarativeBase):
    __tablename__ = 'nodeNote'
    __table_args__ = {}

    #column definitions:
    id = Column(u'id', INTEGER(), primary_key=True, nullable=False)
    node_id = Column(u'node_id', INTEGER(), ForeignKey('node.id'), nullable=False)
    timestamp = Column(u'timestamp', BigInteger(), primary_key=True, nullable=False)
    userid = Column(u'userid', TEXT())
    note = Column(u'note', TEXT())
    token = Column(u'token', VARCHAR(length=31), nullable=False)

    #relation definitions:
    node = relation('Node', primaryjoin='NodeNote.node_id==Node.id')

#
# class Token
# Used to record server tokens.
#
class Token(DeclarativeBase):
    __tablename__ = 'token'
    __table_args__ = {}
    id = Column(u'id', INTEGER(), primary_key=True, nullable=False)
    token = Column(u'token', VARCHAR(length=31), unique=True, nullable=False)
    def __init__(self, token):
        self.token = token

    @staticmethod
    def getTokenId(dbc, token):
    # Returns token id for token, creating new record if necessary.
        try:
            return dbc.query(Token).filter(Token.token == token).one().id
        except sqlalchemy.orm.exc.NoResultFound:
            # Make new token
            nt = Token(token)
            dbc.add(nt)
            dbc.commit()
            return nt.id

#
# class TokenNode
# Used to record nodes created from devices, so as to avoid creating multiple copies.
#
class TokenNode(DeclarativeBase):
    __tablename__ = 'tokenNode'
    __table_args__ = {}
    token_id = Column(u'token_id', INTEGER(), primary_key=True, nullable=False)
    localId = Column(u'localId', INTEGER(), unique=True, nullable=False)
    node_id = Column(u'node_id', INTEGER(), ForeignKey('node.id'), primary_key=True, nullable=False)
    UniqueConstraint(token_id, localId)
    def __init__(self, tokenId, localId, nodeId):
        self.token_id = tokenId
        self.localId = localId
        self.node_id = nodeId

    @staticmethod
    def getOrCreateClientNode(dbc, tokenId, localId, trialId):
    # Create new tokenNode from given token and client local id, if not already created.
    # Returns the id of the new Node, or the already existing one.
    # MFK should trial Id be determined by token?
        try:
            tokNode =  dbc.query(TokenNode).filter(
                and_(TokenNode.token_id == tokenId, TokenNode.localId == localId)).one()
            return tokNode.node_id
        except sqlalchemy.orm.exc.NoResultFound:
            # Make new node
            newNode = Node()
            newNode.trial_id = trialId
            newNode.row = -1
            newNode.col = -1
            dbc.add(newNode)
            dbc.commit() # commit to get the id

            # Create TokenNode
            newtn = TokenNode(tokenId, localId, newNode.id)
            dbc.add(newtn)
            dbc.commit()
            return newNode.id


###  Functions:  ##################################################################################################

gdbg = True

def GetEngineForApp(targetUser):
#-----------------------------------------------------------------------
# This should be called once only and the result stored,
# currently done in session module.
#
    APPUSR = 'fpwserver'
    APPPWD = 'fpws_g00d10ch'
    dbname = 'fp_' + targetUser
    engine = create_engine('mysql://{0}:{1}@localhost/{2}'.format(APPUSR, APPPWD, dbname))
    Session = sessionmaker(bind=engine)
    dbsess = Session()
    return dbsess


# This should use alchemy and return connection
def DbConnectAndAuthenticate(username, password):
#-------------------------------------------------------------------------------------------------
    dbc = GetEngineForApp(username)    # not sure how this returns error, test..
    if dbc is None:
        return (None, 'Unknown user/database')

    # Check login:
    try:
        sysPwRec = dbc.query(System).filter(System.name == 'appPassword').one()
    except sqlalchemy.orm.exc.NoResultFound:
        # No password means OK to use:
        return dbc, None
    except sqlalchemy.orm.exc.MultipleResultsFound:
        # Shouldn't happen:
        return None, 'DB error, multiple passwords'

    if sysPwRec.value == password:
        return dbc, None
    return None, 'Invalid password'


def GetTrial(dbc, trialid):
#-------------------------------------------------------------------------------------------------
    try:
        trl = dbc.query(Trial).filter(Trial.id == trialid).one()
    except sqlalchemy.exc.SQLAlchemyError, e:
        return None
    return trl

def getTrait(dbc, traitId):
#-------------------------------------------------------------------------------------------------
    try:
        trt = dbc.query(Trait).filter(Trait.id == traitId).one()
    except sqlalchemy.exc.SQLAlchemyError, e:
        return None
    return trt

def getTrialTrait(dbc, trialId, traitId):
#-------------------------------------------------------------------------------------------------
    return dbc.query(TrialTrait).filter(
        and_(TrialTrait.trait_id == traitId, TrialTrait.trial_id == trialId)).one()


def GetTrialList(dbc):
#-------------------------------------------------------------------------------------------------
    try:
        trlList = dbc.query(Trial).all()
    except sqlalchemy.exc.SQLAlchemyError, e:
        return None
    return trlList


def GetOrCreateTraitInstance(dbc, traitID, trialID, seqNum, sampleNum, dayCreated, token):
#-------------------------------------------------------------------------------------------------
# Get the trait instance, if it exists, else make a new one,
# In either case, we need the id.
# Note how trait instances from different devices are handled
# Trait instances are uniquely identified by trial/trait/seqNum/sampleNum and token.
    util.flog("GetOrCreateTraitInstance: {0} {1} {2} {3} {4} {5}".format(traitID, trialID, seqNum, sampleNum, dayCreated, token))
    tiSet = dbc.query(TraitInstance).filter(and_(
            TraitInstance.trait_id == traitID,
            TraitInstance.trial_id == trialID,
            TraitInstance.seqNum == seqNum,
            TraitInstance.sampleNum == sampleNum,
            TraitInstance.token == token,
            TraitInstance.dayCreated == dayCreated
            )).all()
    if len(tiSet) == 1:
        dbTi = tiSet[0]
    elif len(tiSet) == 0:
        dbTi = TraitInstance()
        dbTi.trial_id = trialID
        dbTi.trait_id = traitID
        dbTi.dayCreated = dayCreated
        dbTi.seqNum = seqNum
        dbTi.sampleNum = sampleNum
        dbTi.token = token
        dbc.add(dbTi)
        dbc.commit()
    else:
        return None
    return dbTi


def AddTraitInstanceData(dbc, tiID, trtType, aData):
#-------------------------------------------------------------------------------------------------
# Insert or update datum records for specified trait instance.
# Params:
# dbc - db connection
# tiID - id of trait instance
# trtType - type of trait instance
# aData - array of data values, json from device
#
# Return None for success, else an error message.
#
    # Construct list of dictionaries of values to insert:
    try:
        valueFieldName = 'txtValue' if  trtType == T_STRING or trtType == T_PHOTO else 'numValue'
        dlist = []

        for jdat in aData:
            dlist.append({
                 'node_id' : (jdat.get(jDataUpload['node_id']) or jdat.get('trialUnit_id')),
                 'traitInstance_id' : tiID,
                 'timestamp' : jdat[jDataUpload['timestamp']],
                 'gps_long' : jdat[jDataUpload['gps_long']],
                 'gps_lat' : jdat[jDataUpload['gps_lat']],
                 'userid' : jdat[jDataUpload['userid']],
                 valueFieldName : jdat[jDataUpload['value']] if jDataUpload['value'] in jdat else None
            })
        # Note we use ignore because the same data items may be uploaded more than
        # once, and this should not cause the insert to fail.
        insob = datum.insert().prefix_with("ignore")
        res = dbc.execute(insob, dlist)
        dbc.commit()
        return None
    except Exception, e:
        return "An error occurred"

def AddTraitInstanceDatum(dbc, tiID, trtType, nodeId, timestamp, userid, gpslat, gpslong, value):
#-------------------------------------------------------------------------------------------------
# Insert or update datum records for specified trait instance.
# Params:
# dbc - db connection
# tiID - id of trait instance
# trtType - type of trait instance
# aData - array of data values, json from device
#
# Return None for success, else an error message.
#
    # Construct list of dictionaries of values to insert:
    try:
        valueFieldName = Datum.valueFieldName(trtType)
        ins = datum.insert().prefix_with('ignore').values({
             DM_NODE_ID: nodeId,
             DM_TRAITINSTANCE_ID : tiID,
             DM_TIMESTAMP : timestamp,
             DM_GPS_LONG : gpslong,
             DM_GPS_LAT : gpslat,
             DM_USERID : userid,
             valueFieldName : value
        })
        res = dbc.execute(ins)
        dbc.commit()
        return None
    except Exception, e:
        util.flog('AddTraitInstanceDatum: {0},{1},{2},{3},{4},{5}'.format(tiID,trtType,nodeId,timestamp, userid, gpslat))
        util.flog(e.__doc__)
        util.flog(e.message)
        return "An error occurred"

def AddNodeNotes(dbc, token, notes):
#-------------------------------------------------------------------------------------------------
# Return None for success, else an error message.
#
    qry = 'insert ignore into {0} ({1}, {2}, {3}, {4}, {5}) values '.format(
        'nodeNote', 'node_id', 'timestamp', 'userid', 'token', 'note')
    if len(notes) <= 0:
        return None
    for n in notes:
        try:
            nodeId =  n.get(jNotesUpload['node_id']) or n.get('trialUnit_id')
            qry += '({0}, {1}, "{2}", "{3}", "{4}"),'.format(
                nodeId, n[jNotesUpload['timestamp']],
                n[jNotesUpload['userid']], token, n[jNotesUpload['note']])
            # Should be this, but have to cope with 'trialUnit_id' coming
            # from clients for a while..
            # qry += '({0}, {1}, "{2}", "{3}", "{4}"),'.format(
            #     n[jNotesUpload['node_id']], n[jNotesUpload['timestamp']],
            #     n[jNotesUpload['userid']], token, n[jNotesUpload['note']])
        except Exception, e:
            return 'Error parsing note ' + e.args[0]

    qry = qry[:-1] # Remove last comma
    # call sql to do multi insert:
    dbc.bind.execute(qry)
    return None;


def CreateTrait2(dbc, caption, description, vtype, sysType, vmin, vmax):
#--------------------------------------------------------------------------
# Creates a trait with the passed values and writes it to the db.
# Returns a list [ <new trait> | None, ErrorMessage | None ]
# NB doesn't add to trialTrait table
# Currently only written with adhoc traits in mind..
#
    # We need to check that caption is unique within the trial - for local anyway, or is this at the add to trialTrait stage?
    # For creation of a system trait, there is not an automatic adding to a trial, so the uniqueness-within-trial test
    # can wait til the adding stage.
    ntrt = Trait()
    ntrt.caption = caption
    ntrt.description = description
    ntrt.sysType = sysType

    # Check for duplicate captions, probably needs to use transactions or something, but this will usually work:
    # and add to trialTrait?
    if sysType == SYSTYPE_TRIAL: # If local, check there's no other trait local to the trial with the same caption:
        # trial = GetTrialFromDBsess(sess, tid)
        # for x in trial.traits:
        #     if x.caption == caption:
        #         return (None, "Duplicate caption")
        # ntrt.trials = [trial]      # Add the trait to the trial (table trialTrait)
        pass
    elif sysType == SYSTYPE_SYSTEM:  # If system trait, check there's no other system trait with same caption:
        # sysTraits = dbUtil.GetSysTraits(sess)
        # for x in sysTraits:
        #     if x.caption == caption:
        #         return (None, "Duplicate caption")
        pass
    elif sysType == SYSTYPE_ADHOC:
        # Check no trait with same caption that's not an adhoc trait for another device
        # Do adhoc traits go into trialTrait?
        # Perhaps not at the moment, but perhaps they should be..
        pass
    else:
        return (None, "Invalid sysType")

    ntrt.type = vtype
    if vmin:
        ntrt.min = vmin
    if vmax:
        ntrt.max = vmax
    dbc.add(ntrt)
    dbc.commit()
    return ntrt, None

#MFK these functions should probably be replace by method on trait.
# Something generic like get trial trait json details.
def GetTrialTraitNumericDetails(dbc, trait_id, trial_id):
# Return TrialTraitNumeric for specified trait/trial, or None if none exists.
    tti = dbc.query(TrialTraitNumeric).filter(and_(
            TrialTraitNumeric.trait_id == trait_id,
            TrialTraitNumeric.trial_id == trial_id
            )).all()
    if len(tti) == 1:
        ttid = tti[0]
        return ttid
    return None

def getTraitString(dbc, trait_id, trial_id):
# Return TraitString for specified trait/trial, or None if none exists.
    print 'trial {0} trait {1}'.format(trial_id, trait_id)
    ttlist = dbc.query(TraitString).filter(and_(
            TraitString.trait_id == trait_id,
            TraitString.trial_id == trial_id
            )).all()
    if len(ttlist) == 1:
        return ttlist[0]
    return None


def photoFileName(dbusername, trialId, traitId, nodeId, token, seqNum, sampNum):
# Return the file name (not including directory) of the photo for the score with the specified attributes.
    return '{0}_{1}_{2}_{3}_{4}_{5}_{6}.jpg'.format(dbusername, trialId, traitId, nodeId, token, seqNum, sampNum)

